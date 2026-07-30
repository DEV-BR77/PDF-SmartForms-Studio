"""Visual PDF analysis with accessible field states."""

from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from uuid import uuid4

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QDesktopServices,
    QFont,
    QImage,
    QMouseEvent,
    QPen,
    QPixmap,
    QResizeEvent,
    QShowEvent,
)
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGraphicsItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneWheelEvent,
    QGraphicsView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from pdf_smartforms.build_info import __version__
from pdf_smartforms.distribution.document_exporter import export_work_copy
from pdf_smartforms.distribution.email_draft import create_email_draft
from pdf_smartforms.distribution.metadata import suggest_communication
from pdf_smartforms.domain.detection import AnalysisResult, DetectedField, MatchStatus
from pdf_smartforms.domain.distribution import PlacedSignature, PlacedText
from pdf_smartforms.domain.field_dictionary import SOURCE_LABELS, AliasConflict
from pdf_smartforms.domain.profiles import CustomField, Profile
from pdf_smartforms.domain.safety import SafetyReview
from pdf_smartforms.domain.templates import (
    Rect,
    Template,
    TemplateField,
    TemplateFieldType,
    TemplateStatus,
)
from pdf_smartforms.field_dictionary.repository import FieldDictionaryRepository
from pdf_smartforms.infrastructure.temporary import temporary_workspace
from pdf_smartforms.pdf.analyzer import analyze_pdf, render_page
from pdf_smartforms.printing.service import PdfPrintError, print_pdf
from pdf_smartforms.profiles.repository import ProfileRepository
from pdf_smartforms.profiles.values import profile_value
from pdf_smartforms.signatures.repository import SignatureRepository
from pdf_smartforms.templates.package_builder import build_template_package
from pdf_smartforms.templates.pdf24_import import load_pdf24_form_spec
from pdf_smartforms.templates.repository import TemplateRepository
from pdf_smartforms.ui.profile_editor import ProfileEditorDialog
from pdf_smartforms.ui.safety_review_dialog import confirm_safety_review
from pdf_smartforms.ui.signature_manager import SignatureManagerDialog

_COLORS = {
    MatchStatus.MAPPED: QColor("#1f9d55"),
    MatchStatus.UNCERTAIN: QColor("#d79614"),
    MatchStatus.MISSING: QColor("#d33c3c"),
}


@dataclass(slots=True)
class SignaturePlacementState:
    asset_id: str
    page: int
    x: float
    y: float
    scale: float


class SignatureOverlayItem(QGraphicsPixmapItem):
    """Movable signature preview; mouse wheel scales the selected image."""

    def __init__(self, pixmap: QPixmap, state: SignaturePlacementState) -> None:
        super().__init__(pixmap)
        self.state = state
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setPos(state.x, state.y)
        self.setScale(state.scale)
        self.setToolTip(
            "Unterschriftsbild · mit der Maus verschieben · "
            "mit dem Mausrad über dem Bild skalieren"
        )

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: object) -> object:
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            position = self.pos()
            self.state.x = position.x()
            self.state.y = position.y()
        return result

    def wheelEvent(self, event: QGraphicsSceneWheelEvent | None) -> None:
        if event is None:
            return
        factor = 1.08 if event.delta() > 0 else 1 / 1.08
        self.state.scale = min(3.0, max(0.05, self.state.scale * factor))
        self.setScale(self.state.scale)
        event.accept()


class FitGraphicsView(QGraphicsView):
    """Keep the complete PDF page visible until the user zooms manually."""

    rectangle_created = pyqtSignal(QRectF)

    def __init__(self, scene: QGraphicsScene, parent: QWidget | None = None) -> None:
        super().__init__(scene, parent)
        self.auto_fit = True
        self.page_rect = QRectF()
        self.draw_start: QPointF | None = None
        self.draw_preview: QGraphicsRectItem | None = None
        self.drawing_field = False

    def fit_page(self) -> None:
        self.auto_fit = True
        self.resetTransform()
        if not self.page_rect.isEmpty():
            self.fitInView(self.page_rect, Qt.AspectRatioMode.KeepAspectRatio)

    def set_page_rect(self, rect: QRectF) -> None:
        self.page_rect = rect
        self.setSceneRect(rect)
        QTimer.singleShot(0, self.fit_page)

    def zoom(self, factor: float) -> None:
        self.auto_fit = False
        self.scale(factor, factor)

    def begin_field_draw(self) -> None:
        self.drawing_field = True
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            return
        if self.drawing_field and event.button() == Qt.MouseButton.LeftButton:
            position = self.mapToScene(event.position().toPoint())
            if self.page_rect.contains(position):
                self.draw_start = position
                scene = self.scene()
                if scene is not None:
                    self.draw_preview = scene.addRect(
                        QRectF(position, position),
                        QPen(QColor("#235dcc"), 2, Qt.PenStyle.DashLine),
                    )
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            return
        if self.draw_start is not None and self.draw_preview is not None:
            current = self.mapToScene(event.position().toPoint())
            self.draw_preview.setRect(QRectF(self.draw_start, current).normalized())
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            return
        if self.draw_start is not None and self.draw_preview is not None:
            rectangle = self.draw_preview.rect().normalized().intersected(self.page_rect)
            scene = self.scene()
            if scene is not None:
                scene.removeItem(self.draw_preview)
            self.draw_start = None
            self.draw_preview = None
            self.drawing_field = False
            self.unsetCursor()
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            if rectangle.width() >= 6 and rectangle.height() >= 6:
                self.rectangle_created.emit(rectangle)
            return
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        super().resizeEvent(event)
        if self.auto_fit:
            QTimer.singleShot(0, self.fit_page)

    def showEvent(self, event: QShowEvent | None) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self.fit_page)


class PdfAnalysisDialog(QDialog):
    """Display a rendered PDF with non-printing field overlays."""

    SCALE = 1.5

    def __init__(
        self,
        pdf_path: Path,
        dictionary_repository: FieldDictionaryRepository,
        signature_repository: SignatureRepository,
        profile_repository: ProfileRepository,
        template_repository: TemplateRepository,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.dictionary_repository = dictionary_repository
        self.signature_repository = signature_repository
        self.profile_repository = profile_repository
        self.template_repository = template_repository
        self.analysis = analyze_pdf(pdf_path, dictionary_repository.load())
        self.communication = suggest_communication(pdf_path)
        self.signature_placements: list[SignaturePlacementState] = []
        self.current_page = 0
        self.overlay_items: dict[str, QGraphicsRectItem] = {}
        self.signature_items: list[SignatureOverlayItem] = []
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowTitle(f"PDF analysieren · {self.communication.title} · Version {__version__}")
        self.resize(1500, 900)
        self._build_ui()
        self._populate_field_list()
        self._show_page(0)
        if self.analysis.warnings:
            QMessageBox.information(self, "Analysehinweis", "\n".join(self.analysis.warnings))

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        title = QLabel(self.communication.title)
        title.setObjectName("title")
        top.addWidget(title)
        top.addStretch()
        zoom_out = QPushButton("−")
        zoom_out.setAccessibleName("Vorschau verkleinern")
        zoom_out.clicked.connect(lambda: self.view.zoom(1 / 1.15))
        zoom_in = QPushButton("+")
        zoom_in.setAccessibleName("Vorschau vergrößern")
        zoom_in.clicked.connect(lambda: self.view.zoom(1.15))
        fit_page = QPushButton("Seite")
        fit_page.setAccessibleName("Ganze PDF-Seite in die Vorschau einpassen")
        fit_page.clicked.connect(lambda: self.view.fit_page())
        self.previous_button = QPushButton("←")
        self.previous_button.setAccessibleName("Vorherige Seite")
        self.previous_button.clicked.connect(self._previous_page)
        self.page_label = QLabel()
        self.next_button = QPushButton("→")
        self.next_button.setAccessibleName("Nächste Seite")
        self.next_button.clicked.connect(self._next_page)
        for widget in (
            zoom_out,
            zoom_in,
            fit_page,
            self.previous_button,
            self.page_label,
            self.next_button,
        ):
            top.addWidget(widget)
        layout.addLayout(top)

        splitter = QSplitter()
        self.scene = QGraphicsScene(self)
        self.scene.selectionChanged.connect(self._sync_scene_selection)
        self.view = FitGraphicsView(self.scene)
        self.view.rectangle_created.connect(self._create_manual_field)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        field_panel = QWidget()
        field_layout = QVBoxLayout(field_panel)
        field_layout.addWidget(QLabel("<b>Erkannte Felder</b>"))
        legend = QLabel(
            "✓ Grün: zugeordnet\n"
            "⚠ Gelb: Prüfung erforderlich\n"
            "✕ Rot: nicht zugeordnet\n"
            "▣ Blau: aktuell ausgewählt"
        )
        field_layout.addWidget(legend)
        self.field_list = QListWidget()
        self.field_list.currentItemChanged.connect(self._focus_selected_field)
        field_layout.addWidget(self.field_list, 1)
        add_field = QPushButton("Feld auf PDF aufziehen")
        add_field.clicked.connect(self._begin_manual_field)
        field_layout.addWidget(add_field)
        self.show_all_frames = QCheckBox("Alle Feldrahmen anzeigen")
        self.show_all_frames.setChecked(False)
        self.show_all_frames.toggled.connect(self._update_overlay_visibility)
        field_layout.addWidget(self.show_all_frames)
        save_template = QPushButton("Korrigierte Felder als Vorlage speichern")
        save_template.setToolTip(
            "Speichert die aktuelle Erkennung samt manueller Korrekturen "
            "als wiederverwendbare lokale Vorlage"
        )
        save_template.clicked.connect(self._save_as_template)
        field_layout.addWidget(save_template)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        field_layout.addWidget(self.summary)
        splitter.addWidget(field_panel)
        splitter.addWidget(self.view)

        side = QWidget()
        side_layout = QVBoxLayout(side)
        side_layout.addWidget(QLabel("Profil für Vorschau und Ausgabe"))
        self.profile_combo = QComboBox()
        self._reload_profiles()
        self.profile_combo.currentIndexChanged.connect(
            lambda _index: self._show_page(self.current_page)
        )
        side_layout.addWidget(self.profile_combo)
        side_layout.addWidget(QLabel("<b>Zuordnung und Einstellungen</b>"))
        self.source_combo = QComboBox()
        self._reload_source_choices()
        side_layout.addWidget(self.source_combo)
        field_properties = QFormLayout()
        self.detected_type = QComboBox()
        for field_type in TemplateFieldType:
            self.detected_type.addItem(field_type.value, field_type.value)
        self.detected_x = self._coordinate_input()
        self.detected_y = self._coordinate_input()
        self.detected_width = self._coordinate_input(1.0)
        self.detected_height = self._coordinate_input(1.0)
        field_properties.addRow("Feldtyp", self.detected_type)
        field_properties.addRow("X", self.detected_x)
        field_properties.addRow("Y", self.detected_y)
        field_properties.addRow("Breite", self.detected_width)
        field_properties.addRow("Höhe", self.detected_height)
        side_layout.addLayout(field_properties)
        apply_geometry = QPushButton("Position und Größe übernehmen")
        apply_geometry.clicked.connect(self._apply_selected_geometry)
        side_layout.addWidget(apply_geometry)
        create_profile_field = QPushButton("Neues Profilfeld für diese Angabe")
        create_profile_field.clicked.connect(self._create_custom_profile_field)
        side_layout.addWidget(create_profile_field)
        self.learn_alias = QCheckBox("Diese Zuordnung künftig lokal erkennen")
        self.learn_alias.setChecked(True)
        side_layout.addWidget(self.learn_alias)
        apply_mapping = QPushButton("Zuordnung übernehmen")
        apply_mapping.setObjectName("primary")
        apply_mapping.clicked.connect(self._apply_manual_mapping)
        side_layout.addWidget(apply_mapping)
        remove_detection = QPushButton("Erkennung entfernen")
        remove_detection.setToolTip(
            "Den markierten Vorschlag nur aus dieser Dokumentanalyse entfernen"
        )
        remove_detection.clicked.connect(self._remove_selected_detection)
        side_layout.addWidget(remove_detection)
        dictionary_actions = QHBoxLayout()
        import_pdf24 = QPushButton("PDF24-Felder")
        import_pdf24.clicked.connect(self._import_pdf24_fields)
        import_dictionary = QPushButton("Lexikon importieren")
        import_dictionary.clicked.connect(self._import_dictionary)
        export_dictionary = QPushButton("Lexikon exportieren")
        export_dictionary.clicked.connect(self._export_dictionary)
        dictionary_actions.addWidget(import_pdf24)
        dictionary_actions.addWidget(import_dictionary)
        dictionary_actions.addWidget(export_dictionary)
        side_layout.addLayout(dictionary_actions)
        side_layout.addWidget(QLabel("Unterschriftsbild"))
        self.signature_combo = QComboBox()
        self._reload_signatures()
        side_layout.addWidget(self.signature_combo)
        add_signature = QPushButton("Unterschrift auf Seite einfügen")
        add_signature.clicked.connect(self._add_signature)
        side_layout.addWidget(add_signature)
        self.signature_scale = QSlider(Qt.Orientation.Horizontal)
        self.signature_scale.setRange(5, 200)
        self.signature_scale.setValue(100)
        self.signature_scale.setEnabled(False)
        self.signature_scale.setToolTip("Größe der ausgewählten Unterschrift")
        self.signature_scale.valueChanged.connect(self._change_signature_scale)
        side_layout.addWidget(QLabel("Größe der ausgewählten Unterschrift"))
        side_layout.addWidget(self.signature_scale)
        remove_signature = QPushButton("Ausgewählte Unterschrift löschen")
        remove_signature.clicked.connect(self._remove_selected_signature)
        side_layout.addWidget(remove_signature)
        signature_hint = QLabel(
            "Bild mit der Maus verschieben; Mausrad über dem Bild skaliert. "
            "Dies ist keine qualifizierte elektronische Signatur."
        )
        signature_hint.setWordWrap(True)
        side_layout.addWidget(signature_hint)
        side_layout.addWidget(QLabel("Ausgabe und E-Mail-Entwurf"))
        self.recipient_edit = QLineEdit(", ".join(self.communication.recipients))
        self.recipient_edit.setPlaceholderText("Empfänger prüfen")
        self.subject_edit = QLineEdit(self.communication.subject)
        side_layout.addWidget(self.recipient_edit)
        side_layout.addWidget(self.subject_edit)
        output_actions = QHBoxLayout()
        save_pdf = QPushButton("Speichern")
        save_pdf.clicked.connect(self._save_work_copy)
        print_pdf = QPushButton("Drucken")
        print_pdf.clicked.connect(self._print_work_copy)
        email_draft = QPushButton("E-Mail-Entwurf")
        email_draft.clicked.connect(self._create_email_draft)
        output_actions.addWidget(save_pdf)
        output_actions.addWidget(print_pdf)
        output_actions.addWidget(email_draft)
        side_layout.addLayout(output_actions)
        side_layout.addStretch()
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        settings_scroll.setWidget(side)
        splitter.addWidget(settings_scroll)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([300, 820, 360])
        layout.addWidget(splitter)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_button = buttons.button(QDialogButtonBox.StandardButton.Close)
        if close_button is not None:
            close_button.setText("Schließen")
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _coordinate_input(minimum: float = 0.0) -> QDoubleSpinBox:
        value = QDoubleSpinBox()
        value.setRange(minimum, 5000.0)
        value.setDecimals(1)
        value.setSingleStep(1.0)
        value.setSuffix(" pt")
        return value

    def _populate_field_list(self) -> None:
        self.field_list.clear()
        for field in self.analysis.fields:
            item = QListWidgetItem(
                f"{field.status_label} · Seite {field.page + 1}\n"
                f"{field.label} → {field.source or 'keine Zuordnung'}\n"
                f"{field.type.value} · {field.origin} · "
                f"x={field.rect.x0:.0f}, y={field.rect.y0:.0f}, "
                f"{field.rect.width:.0f}×{field.rect.height:.0f} pt"
            )
            item.setData(Qt.ItemDataRole.UserRole, field.id)
            item.setForeground(_COLORS[field.status])
            self.field_list.addItem(item)
        counts = {
            status: sum(field.status == status for field in self.analysis.fields)
            for status in MatchStatus
        }
        self.summary.setText(
            f"{len(self.analysis.fields)} Felder erkannt · "
            f"{counts[MatchStatus.MAPPED]} zugeordnet · "
            f"{counts[MatchStatus.UNCERTAIN]} zu prüfen · "
            f"{counts[MatchStatus.MISSING]} nicht zugeordnet"
        )

    def _show_page(self, page_number: int) -> None:
        selected = self._selected_field()
        selected_id = selected.id if selected is not None else ""
        self.current_page = page_number
        samples, width, height = render_page(self.pdf_path, page_number, self.SCALE)
        image = QImage(samples, width, height, width * 3, QImage.Format.Format_RGB888).copy()
        self.scene.clear()
        self.overlay_items.clear()
        self.signature_items.clear()
        self.scene.addItem(QGraphicsPixmapItem(QPixmap.fromImage(image)))
        for field in self.analysis.fields:
            if field.page != page_number:
                continue
            rect = field.rect
            item = self.scene.addRect(
                rect.x0 * self.SCALE,
                rect.y0 * self.SCALE,
                rect.width * self.SCALE,
                rect.height * self.SCALE,
                QPen(_COLORS[field.status], 1),
            )
            assert item is not None
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
            item.setData(0, field.id)
            item.setVisible(self.show_all_frames.isChecked() or field.id == selected_id)
            item.setToolTip(
                f"{field.status_label}\n{field.label}\n"
                f"Quelle: {field.source or 'nicht zugeordnet'}\n"
                f"Konfidenz: {field.confidence:.0%}"
            )
            self.overlay_items[field.id] = item
            value = self._value_for_field(field)
            if value:
                text_item = self.scene.addText(value)
                assert text_item is not None
                text_item.setFont(QFont("Arial", 8))
                text_item.setDefaultTextColor(QColor("#102a43"))
                text_item.setPos(
                    (rect.x0 + 2) * self.SCALE,
                    (rect.y0 + 1) * self.SCALE,
                )
                text_item.setScale(self.SCALE)
                text_item.setTextWidth(max(20, rect.width - 4))
                text_item.setZValue(5)
        self._render_signature_placements()
        self.view.set_page_rect(QRectF(0, 0, width, height))
        self.page_label.setText(f"Seite {page_number + 1} von {self.analysis.page_count}")
        self.previous_button.setEnabled(page_number > 0)
        self.next_button.setEnabled(page_number + 1 < self.analysis.page_count)

    def _field_by_id(self, field_id: str) -> DetectedField | None:
        return next((field for field in self.analysis.fields if field.id == field_id), None)

    def _focus_selected_field(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            return
        field = self._field_by_id(str(current.data(Qt.ItemDataRole.UserRole)))
        if field is None:
            return
        if field.source:
            source_index = self.source_combo.findData(field.source)
            if source_index >= 0:
                self.source_combo.setCurrentIndex(source_index)
        else:
            self.source_combo.setCurrentIndex(0)
        type_index = self.detected_type.findData(field.type.value)
        self.detected_type.setCurrentIndex(max(0, type_index))
        self.detected_x.setValue(field.rect.x0)
        self.detected_y.setValue(field.rect.y0)
        self.detected_width.setValue(field.rect.width)
        self.detected_height.setValue(field.rect.height)
        if field.page != self.current_page:
            self._show_page(field.page)
        overlay = self.overlay_items.get(field.id)
        if overlay is not None:
            for candidate in self.analysis.fields:
                candidate_overlay = self.overlay_items.get(candidate.id)
                if candidate_overlay is not None:
                    candidate_overlay.setPen(QPen(_COLORS[candidate.status], 1))
                    candidate_overlay.setVisible(self.show_all_frames.isChecked())
                    candidate_overlay.setZValue(0)
            self.view.centerOn(overlay)
            overlay.setVisible(True)
            overlay.setPen(QPen(QColor("#235dcc"), 3))
            overlay.setZValue(10)
            overlay.setSelected(True)

    def _selected_field(self) -> DetectedField | None:
        item = self.field_list.currentItem()
        if item is None:
            return None
        return self._field_by_id(str(item.data(Qt.ItemDataRole.UserRole)))

    def _sync_scene_selection(self) -> None:
        self._sync_signature_controls()
        for item in self.scene.selectedItems():
            field_id = item.data(0)
            if not isinstance(field_id, str):
                continue
            for index in range(self.field_list.count()):
                list_item = self.field_list.item(index)
                if (
                    list_item is not None
                    and str(list_item.data(Qt.ItemDataRole.UserRole)) == field_id
                ):
                    self.field_list.setCurrentItem(list_item)
                    return

    def _update_overlay_visibility(self) -> None:
        selected = self._selected_field()
        selected_id = selected.id if selected is not None else ""
        for field_id, item in self.overlay_items.items():
            item.setVisible(self.show_all_frames.isChecked() or field_id == selected_id)

    def _begin_manual_field(self) -> None:
        self.view.begin_field_draw()
        QMessageBox.information(
            self,
            "Feld aufziehen",
            "Ziehe jetzt mit gedrückter linker Maustaste einen Rahmen auf der PDF-Seite auf.",
        )

    def _create_manual_field(self, rectangle: QRectF) -> None:
        label, accepted = QInputDialog.getText(
            self,
            "Neues Formularfeld",
            "Welche Angabe gehört in dieses Feld?",
        )
        if not accepted or not label.strip():
            return
        labels = {
            TemplateFieldType.TEXT: "Text",
            TemplateFieldType.MULTILINE: "Mehrzeiliger Text",
            TemplateFieldType.DATE: "Datum",
            TemplateFieldType.CHECKBOX: "Kontrollkästchen",
            TemplateFieldType.RADIO: "Ja/Nein oder Optionsfeld",
            TemplateFieldType.CHOICE: "Auswahlliste",
            TemplateFieldType.SIGNATURE_IMAGE: "Unterschriftsbild",
            TemplateFieldType.DIGITAL_SIGNATURE: "Digitales Signaturfeld",
        }
        type_names = list(labels.values())
        selected_type, accepted = QInputDialog.getItem(
            self,
            "Feldtyp",
            "Art des Feldes:",
            type_names,
            0,
            False,
        )
        if not accepted:
            return
        field_type = next(key for key, value in labels.items() if value == selected_type)
        pdf_rect = Rect(
            rectangle.left() / self.SCALE,
            rectangle.top() / self.SCALE,
            rectangle.right() / self.SCALE,
            rectangle.bottom() / self.SCALE,
        )
        source, status, confidence = self.dictionary_repository.load().match(label)
        field = DetectedField(
            id=f"manual-{uuid4().hex[:12]}",
            label=label.strip(),
            type=field_type,
            page=self.current_page,
            rect=pdf_rect,
            source=source,
            status=status,
            confidence=confidence,
            origin="Manuell angelegt",
        )
        self.analysis = AnalysisResult(
            self.analysis.title,
            self.analysis.page_count,
            (*self.analysis.fields, field),
            self.analysis.warnings,
        )
        self._populate_field_list()
        self._show_page(self.current_page)
        self._select_field_id(field.id)

    def _select_field_id(self, field_id: str) -> None:
        for index in range(self.field_list.count()):
            item = self.field_list.item(index)
            if item is not None and str(item.data(Qt.ItemDataRole.UserRole)) == field_id:
                self.field_list.setCurrentItem(item)
                return

    def _apply_selected_geometry(self) -> None:
        field = self._selected_field()
        if field is None:
            QMessageBox.information(
                self, "Feld auswählen", "Bitte zuerst ein Feld in der linken Liste auswählen."
            )
            return
        updated = replace(
            field,
            type=TemplateFieldType(str(self.detected_type.currentData())),
            rect=Rect(
                self.detected_x.value(),
                self.detected_y.value(),
                self.detected_x.value() + self.detected_width.value(),
                self.detected_y.value() + self.detected_height.value(),
            ),
            origin=f"{field.origin} · manuell korrigiert",
        )
        self.analysis = AnalysisResult(
            self.analysis.title,
            self.analysis.page_count,
            tuple(updated if item.id == field.id else item for item in self.analysis.fields),
            self.analysis.warnings,
        )
        self._populate_field_list()
        self._show_page(updated.page)
        self._select_field_id(updated.id)

    def _import_pdf24_fields(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "PDF24-Formularfelder importieren",
            "",
            "PDF24-Formularbeschreibung (*.json)",
        )
        if not filename:
            return
        try:
            imported = load_pdf24_form_spec(Path(filename))
        except ValueError as error:
            QMessageBox.warning(self, "Import nicht möglich", str(error))
            return
        dictionary = self.dictionary_repository.load()
        fields: list[DetectedField] = []
        for index, item in enumerate(imported):
            label = str(item["label"])
            source, status, confidence = dictionary.match(label.replace("_", " "))
            fields.append(
                DetectedField(
                    id=f"pdf24-{index}-{item['id']}",
                    label=label,
                    type=item["type"],
                    page=int(item["page"]),
                    rect=item["rect"],
                    source=source,
                    status=status,
                    confidence=confidence,
                    origin="PDF24-Import",
                )
            )
        if not fields:
            QMessageBox.information(self, "Keine Felder", "Die Datei enthält keine Felder.")
            return
        self.analysis = AnalysisResult(
            self.analysis.title,
            self.analysis.page_count,
            tuple(fields),
            self.analysis.warnings,
        )
        self._populate_field_list()
        self._show_page(fields[0].page)
        self._select_field_id(fields[0].id)
        QMessageBox.information(
            self,
            "Formularfelder importiert",
            f"{len(fields)} Felder wurden übernommen und in der Vorschau angezeigt.",
        )

    def _save_as_template(self) -> None:
        """Persist the corrected normal-PDF analysis as a reusable local template."""
        if not self.analysis.fields:
            QMessageBox.information(
                self,
                "Keine Felder",
                "Bitte zuerst mindestens ein Feld erkennen oder auf der PDF-Seite aufziehen.",
            )
            return
        name, accepted = QInputDialog.getText(
            self,
            "Lokale Vorlage speichern",
            "Name der Vorlage:",
            text=self.communication.title,
        )
        if not accepted or not name.strip():
            return
        template_id = re.sub(r"[^a-z0-9._-]+", "-", name.casefold()).strip("-")
        template_id = template_id or f"local-{uuid4().hex[:12]}"
        existing_versions = [
            item.version for item in self.template_repository.list() if item.id == template_id
        ]
        version = f"1.0.{len(existing_versions)}"
        template = Template(
            id=template_id,
            name=name.strip(),
            version=version,
            language="de",
            status=TemplateStatus.LOCAL,
            minimum_app_version=__version__,
            source_pdf=self.pdf_path.name,
            source_pdf_license="Lokale Benutzervorlage",
            fields=[
                TemplateField(
                    id=field.id,
                    label=field.label,
                    type=field.type,
                    page=field.page,
                    rect=field.rect,
                    source=field.source or "",
                )
                for field in self.analysis.fields
            ],
        )
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Vorlagenpaket speichern",
            str(self.pdf_path.with_name(f"{template_id}-{version}.psfstemplate")),
            "PDF SmartForms Vorlage (*.psfstemplate)",
        )
        if not filename:
            return
        target = Path(filename)
        if target.suffix.casefold() != ".psfstemplate":
            target = target.with_suffix(".psfstemplate")
        try:
            package = build_template_package(template, self.pdf_path, target)
            self.template_repository.install_package(package)
        except (FileExistsError, OSError, ValueError) as error:
            QMessageBox.critical(self, "Vorlage nicht gespeichert", str(error))
            return
        QMessageBox.information(
            self,
            "Vorlage gespeichert",
            f"Die korrigierten Felder sind jetzt als lokale Vorlage "
            f"„{template.name}“ ({template.version}) verfügbar.",
        )

    def _apply_manual_mapping(self) -> None:
        field = self._selected_field()
        source = self.source_combo.currentData()
        if field is None or not isinstance(source, str):
            QMessageBox.information(
                self, "Feld auswählen", "Bitte zuerst ein erkanntes Feld auswählen."
            )
            return
        if self.learn_alias.isChecked():
            try:
                self.dictionary_repository.learn(field.label, source)
            except AliasConflict as error:
                QMessageBox.warning(self, "Lexikon-Konflikt", str(error))
                return
        updated = replace(
            field,
            source=source,
            status=MatchStatus.MAPPED,
            confidence=1.0,
            origin="Manuell bestätigt",
        )
        fields = tuple(updated if item.id == field.id else item for item in self.analysis.fields)
        self.analysis = AnalysisResult(
            self.analysis.title,
            self.analysis.page_count,
            fields,
            self.analysis.warnings,
        )
        self._populate_field_list()
        self._show_page(self.current_page)

    def _remove_selected_detection(self) -> None:
        field = self._selected_field()
        if field is None:
            QMessageBox.information(
                self,
                "Erkennung auswählen",
                "Bitte zuerst den Vorschlag auswählen, der kein Formularfeld ist.",
            )
            return
        answer = QMessageBox.question(
            self,
            "Erkennung entfernen",
            f"„{field.label}“ aus dieser Dokumentanalyse entfernen?\n\n"
            "Beim erneuten Öffnen des PDFs wird die Analyse neu durchgeführt.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.analysis = AnalysisResult(
            self.analysis.title,
            self.analysis.page_count,
            tuple(item for item in self.analysis.fields if item.id != field.id),
            self.analysis.warnings,
        )
        self._populate_field_list()
        self._show_page(self.current_page)

    def _import_dictionary(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "Feldlexikon importieren", "", "JSON (*.json)"
        )
        if not filename:
            return
        try:
            report = self.dictionary_repository.import_from(Path(filename))
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "Import fehlgeschlagen", str(error))
            return
        if report.conflicts:
            answer = QMessageBox.question(
                self,
                "Bestehende Zuordnungen ändern?",
                "Einige Begriffe sind bereits anderen Feldern zugeordnet:\n\n"
                + "\n".join(report.conflicts)
                + "\n\nSollen die Zuordnungen aus der importierten Datei diese ersetzen?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer == QMessageBox.StandardButton.Yes:
                report = self.dictionary_repository.import_from(
                    Path(filename), overwrite_conflicts=True
                )
        self._reload_source_choices()
        self._rematch_fields()
        conflict_text = (
            "\n\nNicht ersetzte Konflikte:\n" + "\n".join(report.conflicts)
            if report.conflicts
            else ""
        )
        QMessageBox.information(
            self,
            "Lexikon importiert",
            f"Neu: {report.added}\nBereits vorhanden: {report.duplicates}"
            f"\nKonflikte: {len(report.conflicts)}{conflict_text}",
        )

    def _rematch_fields(self) -> None:
        dictionary = self.dictionary_repository.load()
        fields: list[DetectedField] = []
        for field in self.analysis.fields:
            source, status, confidence = dictionary.match(field.label.replace("_", " "))
            fields.append(
                replace(
                    field,
                    source=source,
                    status=status,
                    confidence=confidence,
                )
            )
        selected = self._selected_field()
        selected_id = selected.id if selected is not None else ""
        self.analysis = AnalysisResult(
            self.analysis.title,
            self.analysis.page_count,
            tuple(fields),
            self.analysis.warnings,
        )
        self._populate_field_list()
        self._show_page(self.current_page)
        if selected_id:
            self._select_field_id(selected_id)

    def _reload_source_choices(self, selected_source: str | None = None) -> None:
        if not hasattr(self, "source_combo"):
            return
        current = selected_source or (
            str(self.source_combo.currentData())
            if isinstance(self.source_combo.currentData(), str)
            else ""
        )
        sources = set(SOURCE_LABELS)
        sources.update(self.dictionary_repository.load().sources())
        profile = self._selected_profile() if hasattr(self, "profile_combo") else None
        custom_labels: dict[str, str] = {}
        if profile is not None:
            for custom in profile.custom_fields:
                sources.add(custom.key)
                custom_labels[custom.key] = custom.label
        self.source_combo.clear()
        self.source_combo.addItem("Bitte Datenquelle auswählen", None)
        choices = [
            (
                source,
                SOURCE_LABELS.get(
                    source,
                    custom_labels.get(
                        source,
                        source.removeprefix("custom.").replace("_", " ").replace(".", " ").title(),
                    ),
                ),
            )
            for source in sources
        ]
        for source, label in sorted(choices, key=lambda item: item[1].casefold()):
            self.source_combo.addItem(label, source)
        index = self.source_combo.findData(current)
        self.source_combo.setCurrentIndex(max(0, index))

    def _create_custom_profile_field(self) -> None:
        field = self._selected_field()
        profile = self._selected_profile()
        if field is None:
            QMessageBox.information(
                self, "Feld auswählen", "Bitte zuerst das neue Formularfeld auswählen."
            )
            return
        if profile is None:
            answer = QMessageBox.question(
                self,
                "Noch kein Profil vorhanden",
                "Für ein dauerhaftes Profilfeld wird ein Profil benötigt.\n\n"
                "Möchtest du jetzt ein Profil anlegen?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            editor = ProfileEditorDialog(parent=self)
            if editor.exec() != QDialog.DialogCode.Accepted:
                return
            self.profile_repository.save(editor.profile)
            self._reload_profiles()
            profile_index = self.profile_combo.findData(editor.profile.id)
            self.profile_combo.setCurrentIndex(max(0, profile_index))
            profile = editor.profile
        label, accepted = QInputDialog.getText(
            self,
            "Neues Profilfeld",
            "Bezeichnung des Profilfelds:",
            text=field.label,
        )
        label = label.strip()
        if not accepted or not label:
            return
        value, accepted = QInputDialog.getText(
            self,
            "Wert übernehmen",
            f"Wert für „{label}“ im Profil „{profile.effective_display_name()}“:",
        )
        if not accepted:
            return
        key = "custom." + re.sub(r"[^a-z0-9]+", "_", label.casefold()).strip("_")
        existing = next((item for item in profile.custom_fields if item.key == key), None)
        if existing is None:
            profile.custom_fields.append(CustomField(key=key, label=label, value=value.strip()))
        else:
            existing.label = label
            existing.value = value.strip()
        self.profile_repository.save(profile)
        self.dictionary_repository.learn(field.label, key)
        self._reload_source_choices(key)
        self._apply_manual_mapping()

    def _export_dictionary(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Feldlexikon exportieren",
            "field-dictionary.de.json",
            "JSON (*.json)",
        )
        if not filename:
            return
        try:
            self.dictionary_repository.export_to(Path(filename))
        except OSError as error:
            QMessageBox.critical(self, "Export fehlgeschlagen", str(error))
            return
        QMessageBox.information(
            self,
            "Lexikon exportiert",
            "Der Export enthält ausschließlich Feldbegriffe und Zuordnungen, keine Profilwerte.",
        )

    def _reload_signatures(self) -> None:
        self.signature_combo.clear()
        for asset in self.signature_repository.list():
            owner = "Person 1" if asset.owner.value == "guardian_1" else "Person 2"
            self.signature_combo.addItem(f"{owner} · {asset.name}", asset.id)

    def _reload_profiles(self) -> None:
        self.profile_combo.clear()
        profiles = self.profile_repository.list()
        if not profiles:
            self.profile_combo.addItem("Kein Profil vorhanden", None)
            return
        for profile in profiles:
            self.profile_combo.addItem(profile.effective_display_name(), profile.id)
        if hasattr(self, "source_combo"):
            self._reload_source_choices()

    def _selected_profile(self) -> Profile | None:
        profile_id = self.profile_combo.currentData()
        return self.profile_repository.get(profile_id) if isinstance(profile_id, str) else None

    def _value_for_field(self, field: DetectedField) -> str:
        return profile_value(self._selected_profile(), field.source, field.label)

    def _add_signature(self) -> None:
        asset_id = self.signature_combo.currentData()
        asset = next(
            (item for item in self.signature_repository.list() if item.id == asset_id),
            None,
        )
        if asset is None:
            SignatureManagerDialog(self.signature_repository, self).exec()
            self._reload_signatures()
            asset_id = self.signature_combo.currentData()
            asset = next(
                (item for item in self.signature_repository.list() if item.id == asset_id),
                None,
            )
            if asset is None:
                return
        pixmap = QPixmap(str(self.signature_repository.image_path(asset)))
        if pixmap.isNull():
            QMessageBox.critical(
                self, "Unterschrift nicht lesbar", "Die gespeicherte Bilddatei fehlt."
            )
            return
        signature_field = next(
            (
                field
                for field in self.analysis.fields
                if field.page == self.current_page
                and (field.source == "signature.date" or "unterschrift" in field.label.casefold())
            ),
            None,
        )
        existing_on_page = sum(
            placement.page == self.current_page for placement in self.signature_placements
        )
        if signature_field is None:
            x, y = 120.0, 160.0
            initial_scale = min(1.0, 180 / max(1, pixmap.width()))
        else:
            rect = signature_field.rect
            slot = min(existing_on_page, 1)
            x = (rect.x0 + rect.width * (0.36 + 0.32 * slot)) * self.SCALE
            y = (rect.y0 + 2) * self.SCALE
            target_width = rect.width * 0.28 * self.SCALE
            target_height = max(10, rect.height - 4) * self.SCALE
            initial_scale = min(
                target_width / max(1, pixmap.width()),
                target_height / max(1, pixmap.height()),
            )
        self.signature_placements.append(
            SignaturePlacementState(
                asset_id=asset.id,
                page=self.current_page,
                x=x,
                y=y,
                scale=initial_scale,
            )
        )
        self._show_page(self.current_page)
        if self.signature_items:
            self.signature_items[-1].setSelected(True)

    def _render_signature_placements(self) -> None:
        assets = {asset.id: asset for asset in self.signature_repository.list()}
        for placement in self.signature_placements:
            if placement.page != self.current_page:
                continue
            asset = assets.get(placement.asset_id)
            if asset is None:
                continue
            pixmap = QPixmap(str(self.signature_repository.image_path(asset)))
            if pixmap.isNull():
                continue
            item = SignatureOverlayItem(pixmap, placement)
            item.setZValue(10)
            self.scene.addItem(item)
            self.signature_items.append(item)

    def _selected_signature_item(self) -> SignatureOverlayItem | None:
        return next(
            (item for item in self.scene.selectedItems() if isinstance(item, SignatureOverlayItem)),
            None,
        )

    def _sync_signature_controls(self) -> None:
        item = self._selected_signature_item()
        self.signature_scale.setEnabled(item is not None)
        if item is not None:
            self.signature_scale.blockSignals(True)
            self.signature_scale.setValue(round(item.state.scale * 100))
            self.signature_scale.blockSignals(False)

    def _change_signature_scale(self, value: int) -> None:
        item = self._selected_signature_item()
        if item is None:
            return
        item.state.scale = value / 100
        item.setScale(item.state.scale)

    def _remove_selected_signature(self) -> None:
        item = self._selected_signature_item()
        if item is None:
            QMessageBox.information(
                self,
                "Unterschrift auswählen",
                "Bitte zuerst die Unterschrift direkt in der PDF-Vorschau anklicken.",
            )
            return
        self.signature_placements = [
            placement for placement in self.signature_placements if placement is not item.state
        ]
        self._show_page(self.current_page)

    def _placed_signatures(self) -> list[PlacedSignature]:
        assets = {asset.id: asset for asset in self.signature_repository.list()}
        output: list[PlacedSignature] = []
        for placement in self.signature_placements:
            asset = assets.get(placement.asset_id)
            if asset is None:
                continue
            width = asset.width * placement.scale / self.SCALE
            height = asset.height * placement.scale / self.SCALE
            x0 = placement.x / self.SCALE
            y0 = placement.y / self.SCALE
            output.append(
                PlacedSignature(
                    str(self.signature_repository.image_path(asset)),
                    placement.page,
                    x0,
                    y0,
                    x0 + width,
                    y0 + height,
                )
            )
        return output

    def _placed_texts(self) -> list[PlacedText]:
        output: list[PlacedText] = []
        for field in self.analysis.fields:
            value = self._value_for_field(field)
            if not value:
                continue
            output.append(
                PlacedText(
                    value,
                    field.page,
                    field.rect.x0,
                    field.rect.y0,
                    field.rect.x1,
                    field.rect.y1,
                )
            )
        return output

    def _safety_review(
        self,
        action: str,
        *,
        recipients: tuple[str, ...] = (),
        subject: str = "",
        attachments: tuple[str, ...] = (),
    ) -> SafetyReview:
        mapped = sum(field.status == MatchStatus.MAPPED for field in self.analysis.fields)
        return SafetyReview(
            action=action,
            document_name=self.pdf_path.name,
            mapped_fields=mapped,
            unresolved_fields=len(self.analysis.fields) - mapped,
            signatures=len(self._placed_signatures()),
            recipients=recipients,
            subject=subject,
            attachments=attachments,
        )

    def _export_to_selected_path(self) -> Path | None:
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "PDF-Arbeitskopie speichern",
            str(self.pdf_path.with_name(f"{self.pdf_path.stem}_ausgefüllt.pdf")),
            "PDF-Dokumente (*.pdf)",
        )
        if not filename:
            return None
        try:
            return export_work_copy(
                self.pdf_path,
                Path(filename),
                self._placed_signatures(),
                self._placed_texts(),
            )
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "PDF konnte nicht gespeichert werden", str(error))
            return None

    def _save_work_copy(self) -> None:
        if not confirm_safety_review(self._safety_review("PDF speichern"), self):
            return
        target = self._export_to_selected_path()
        if target:
            QMessageBox.information(self, "PDF gespeichert", f"Arbeitskopie gespeichert:\n{target}")

    def _print_work_copy(self) -> None:
        if not confirm_safety_review(self._safety_review("PDF drucken"), self):
            return
        try:
            temporary_root = Path(tempfile.gettempdir()) / "PDF-SmartForms-Studio"
            with temporary_workspace(temporary_root) as workspace:
                target = export_work_copy(
                    self.pdf_path,
                    workspace / "print.pdf",
                    self._placed_signatures(),
                    self._placed_texts(),
                )
                printed = print_pdf(target, self)
        except (OSError, ValueError, PdfPrintError) as error:
            QMessageBox.critical(self, "Drucken fehlgeschlagen", str(error))
            return
        if printed:
            QMessageBox.information(
                self,
                "Druckauftrag erstellt",
                "Das Dokument wurde an den ausgewählten Drucker übergeben.",
            )

    def _create_email_draft(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "E-Mail-Entwurf speichern",
            str(self.pdf_path.with_name(f"{self.pdf_path.stem}_E-Mail.eml")),
            "E-Mail-Entwurf (*.eml)",
        )
        if not filename:
            return
        target = Path(filename)
        pdf_target = target.with_suffix(".pdf")
        recipients = [
            item.strip() for item in re.split(r"[,;]", self.recipient_edit.text()) if item.strip()
        ]
        subject = self.subject_edit.text().strip()
        if not confirm_safety_review(
            self._safety_review(
                "E-Mail-Entwurf",
                recipients=tuple(recipients),
                subject=subject,
                attachments=(pdf_target.name,),
            ),
            self,
        ):
            return
        try:
            export_work_copy(
                self.pdf_path,
                pdf_target,
                self._placed_signatures(),
                self._placed_texts(),
            )
            create_email_draft(
                target,
                recipients=recipients,
                subject=subject,
                body=(
                    "Guten Tag,\n\nanbei erhalten Sie das ausgefüllte Formular. "
                    "Bitte prüfen Sie den Anhang.\n\n"
                    "Erstellt mit PDF SmartForms Studio."
                ),
                attachments=[pdf_target],
            )
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "Entwurf konnte nicht erstellt werden", str(error))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    def _previous_page(self) -> None:
        if self.current_page > 0:
            self._show_page(self.current_page - 1)

    def _next_page(self) -> None:
        if self.current_page + 1 < self.analysis.page_count:
            self._show_page(self.current_page + 1)
