"""Visual PDF analysis with accessible field states."""

from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path

from PyQt6.QtCore import QRectF, Qt, QTimer, QUrl
from PyQt6.QtGui import (
    QColor,
    QDesktopServices,
    QFont,
    QImage,
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
    QFileDialog,
    QGraphicsItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneWheelEvent,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
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
from pdf_smartforms.domain.profiles import Profile
from pdf_smartforms.domain.safety import SafetyReview
from pdf_smartforms.field_dictionary.repository import FieldDictionaryRepository
from pdf_smartforms.infrastructure.temporary import temporary_workspace
from pdf_smartforms.pdf.analyzer import analyze_pdf, render_page
from pdf_smartforms.printing.service import PdfPrintError, print_pdf
from pdf_smartforms.profiles.repository import ProfileRepository
from pdf_smartforms.profiles.values import profile_value
from pdf_smartforms.signatures.repository import SignatureRepository
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

    def __init__(self, scene: QGraphicsScene, parent: QWidget | None = None) -> None:
        super().__init__(scene, parent)
        self.auto_fit = True
        self.page_rect = QRectF()

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
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.dictionary_repository = dictionary_repository
        self.signature_repository = signature_repository
        self.profile_repository = profile_repository
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
        self.resize(1180, 760)
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
        self.scene.selectionChanged.connect(self._sync_signature_controls)
        self.view = FitGraphicsView(self.scene)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
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
        side_layout.addWidget(QLabel("Erkannte Felder"))
        legend = QLabel(
            "✓ Grün: zugeordnet\n" "⚠ Gelb: Prüfung erforderlich\n" "✕ Rot: nicht zugeordnet"
        )
        side_layout.addWidget(legend)
        self.field_list = QListWidget()
        self.field_list.setMinimumHeight(190)
        self.field_list.currentItemChanged.connect(self._focus_selected_field)
        side_layout.addWidget(self.field_list, 1)
        side_layout.addWidget(QLabel("Manuelle Zuordnung"))
        self.source_combo = QComboBox()
        self.source_combo.addItem("Bitte Datenquelle auswählen", None)
        for source, label in sorted(SOURCE_LABELS.items(), key=lambda item: item[1]):
            self.source_combo.addItem(label, source)
        side_layout.addWidget(self.source_combo)
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
        import_dictionary = QPushButton("Lexikon importieren")
        import_dictionary.clicked.connect(self._import_dictionary)
        export_dictionary = QPushButton("Lexikon exportieren")
        export_dictionary.clicked.connect(self._export_dictionary)
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
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        side_layout.addWidget(self.summary)
        splitter.addWidget(side)
        splitter.setSizes([820, 320])
        layout.addWidget(splitter)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_button = buttons.button(QDialogButtonBox.StandardButton.Close)
        if close_button is not None:
            close_button.setText("Schließen")
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate_field_list(self) -> None:
        self.field_list.clear()
        for field in self.analysis.fields:
            item = QListWidgetItem(
                f"{field.status_label} · Seite {field.page + 1}\n"
                f"{field.label} → {field.source or 'keine Zuordnung'}"
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
                QPen(_COLORS[field.status], 3),
            )
            assert item is not None
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
        if field.page != self.current_page:
            self._show_page(field.page)
        overlay = self.overlay_items.get(field.id)
        if overlay is not None:
            self.view.centerOn(overlay)
            overlay.setPen(QPen(_COLORS[field.status], 6))

    def _selected_field(self) -> DetectedField | None:
        item = self.field_list.currentItem()
        if item is None:
            return None
        return self._field_by_id(str(item.data(Qt.ItemDataRole.UserRole)))

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
        conflict_text = (
            "\n\nKonflikte wurden nicht überschrieben:\n" + "\n".join(report.conflicts)
            if report.conflicts
            else ""
        )
        QMessageBox.information(
            self,
            "Lexikon importiert",
            f"Neu: {report.added}\nBereits vorhanden: {report.duplicates}"
            f"\nKonflikte: {len(report.conflicts)}{conflict_text}",
        )

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
