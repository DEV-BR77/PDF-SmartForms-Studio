"""Visual template designer."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QColor,
    QImage,
    QKeyEvent,
    QMouseEvent,
    QPen,
    QPixmap,
    QResizeEvent,
    QUndoCommand,
    QUndoStack,
)
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGraphicsItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneHoverEvent,
    QGraphicsSceneMouseEvent,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from pdf_smartforms.domain.field_dictionary import SOURCE_LABELS
from pdf_smartforms.domain.templates import (
    Rect,
    Template,
    TemplateField,
    TemplateFieldType,
    TemplateStatus,
)
from pdf_smartforms.pdf.analyzer import analyze_pdf, render_page
from pdf_smartforms.templates.package_builder import build_template_package
from pdf_smartforms.templates.pdf24_import import load_pdf24_form_spec
from pdf_smartforms.templates.repository import TemplateRepository

_SLUG = re.compile(r"[^a-z0-9._-]+")


@dataclass(slots=True)
class DesignerField:
    id: str
    label: str
    type: TemplateFieldType
    page: int
    rect: Rect
    source: str = ""
    required: bool = False
    option_value: str = ""
    default_value: str = ""
    font_family: str = "Helvetica"
    font_size: float = 9.0


class DesignerFieldItem(QGraphicsRectItem):
    """Movable field rectangle backed by a designer field."""

    def __init__(self, field: DesignerField, on_changed: object) -> None:
        super().__init__(0, 0, field.rect.width, field.rect.height)
        self.field = field
        self.on_changed = on_changed
        self.resizing = False
        self.setPos(field.rect.x0, field.rect.y0)
        self.setAcceptHoverEvents(True)
        self.setPen(QPen(QColor("#235dcc"), 2))
        self.setBrush(QColor(35, 93, 204, 35))
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsFocusable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

    def _in_resize_corner(self, position: QPointF) -> bool:
        return (
            position.x() >= self.rect().right() - 12 and position.y() >= self.rect().bottom() - 12
        )

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent | None) -> None:
        if event is not None:
            self.setCursor(
                Qt.CursorShape.SizeFDiagCursor
                if self._in_resize_corner(event.pos())
                else Qt.CursorShape.SizeAllCursor
            )
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:
        if event is not None and self._in_resize_corner(event.pos()):
            self.resizing = True
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:
        if event is not None and self.resizing:
            position = event.pos()
            self.setRect(0, 0, max(8.0, position.x()), max(8.0, position.y()))
            if callable(self.on_changed):
                self.on_changed(self.field.id)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:
        if self.resizing:
            self.resizing = False
            if event is not None:
                event.accept()
            return
        super().mouseReleaseEvent(event)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: object) -> object:
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            position = self.pos()
            self.field.rect = Rect(
                position.x(),
                position.y(),
                position.x() + self.rect().width(),
                position.y() + self.rect().height(),
            )
            if callable(self.on_changed):
                self.on_changed(self.field.id)
        return result

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if event is None:
            return
        offsets = {
            Qt.Key.Key_Left: (-1, 0),
            Qt.Key.Key_Right: (1, 0),
            Qt.Key.Key_Up: (0, -1),
            Qt.Key.Key_Down: (0, 1),
        }
        key = Qt.Key(event.key())
        if key in offsets:
            dx, dy = offsets[key]
            multiplier = 10 if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 1
            self.moveBy(dx * multiplier, dy * multiplier)
            event.accept()
            return
        super().keyPressEvent(event)


class DesignerView(QGraphicsView):
    """Draw new rectangles by dragging on empty PDF space."""

    rectangle_created = pyqtSignal(QRectF)
    field_selected = pyqtSignal(str)

    def __init__(self, scene: QGraphicsScene) -> None:
        super().__init__(scene)
        self.start: QPointF | None = None
        self.preview: QGraphicsRectItem | None = None
        self.setMouseTracking(True)
        self.setBackgroundBrush(QColor("#454545"))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            position = self.mapToScene(event.position().toPoint())
            scene = self.scene()
            if scene is None:
                return
            item = scene.itemAt(position, self.transform())
            if isinstance(item, QGraphicsPixmapItem):
                self.start = position
                self.preview = scene.addRect(
                    QRectF(position, position),
                    QPen(QColor("#235dcc"), 2, Qt.PenStyle.DashLine),
                )
                return
        super().mousePressEvent(event)
        scene = self.scene()
        selected = scene.selectedItems() if scene is not None else []
        if selected and isinstance(selected[0], DesignerFieldItem):
            self.field_selected.emit(selected[0].field.id)

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            return
        if self.start is not None and self.preview is not None:
            current = self.mapToScene(event.position().toPoint())
            self.preview.setRect(QRectF(self.start, current).normalized())
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            return
        if self.start is not None and self.preview is not None:
            rectangle = self.preview.rect().normalized()
            scene = self.scene()
            if scene is not None:
                scene.removeItem(self.preview)
            self.start = None
            self.preview = None
            if rectangle.width() >= 8 and rectangle.height() >= 8:
                self.rectangle_created.emit(rectangle)
            return
        super().mouseReleaseEvent(event)


class AddFieldCommand(QUndoCommand):
    def __init__(self, designer: TemplateDesignerDialog, field: DesignerField) -> None:
        super().__init__("Feld hinzufügen")
        self.designer = designer
        self.field = field

    def redo(self) -> None:
        self.designer.insert_field(self.field)

    def undo(self) -> None:
        self.designer.remove_field(self.field.id)


class DeleteFieldCommand(QUndoCommand):
    def __init__(self, designer: TemplateDesignerDialog, field: DesignerField) -> None:
        super().__init__("Feld löschen")
        self.designer = designer
        self.field = field

    def redo(self) -> None:
        self.designer.remove_field(self.field.id)

    def undo(self) -> None:
        self.designer.insert_field(self.field)


class TemplateDesignerDialog(QDialog):
    """Create a reusable template by drawing directly on a PDF preview."""

    SCALE = 1.5

    def __init__(
        self,
        pdf_path: Path,
        repository: TemplateRepository,
        parent: QWidget | None = None,
        *,
        existing_template: Template | None = None,
    ) -> None:
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.repository = repository
        self.analysis = analyze_pdf(pdf_path)
        self.current_page = 0
        self.fields: list[DesignerField] = []
        self.items: dict[str, DesignerFieldItem] = {}
        self.undo_stack = QUndoStack(self)
        self.existing_template = existing_template
        self.setWindowTitle(
            "Template bearbeiten" if existing_template is not None else "Neues Template erstellen"
        )
        self.resize(1440, 900)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
        )
        self._build_ui()
        if existing_template is not None:
            for field in existing_template.fields:
                self.fields.append(
                    DesignerField(
                        id=field.id,
                        label=field.label,
                        type=field.type,
                        page=field.page,
                        rect=field.rect,
                        source=field.source,
                        required=field.required,
                        option_value=field.option_value,
                        default_value=field.default_value,
                        font_family=field.font_family,
                        font_size=field.font_size,
                    )
                )
        else:
            for detected in self.analysis.fields:
                self.fields.append(
                    DesignerField(
                        id=detected.id,
                        label=detected.label,
                        type=detected.type,
                        page=detected.page,
                        rect=detected.rect,
                        source=detected.source or "",
                        option_value=detected.option_value,
                        default_value=detected.default_value,
                        font_family=detected.font_family,
                        font_size=detected.font_size,
                    )
                )
        self._refresh_list()
        self._show_page(0)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        toolbar = QToolBar()
        toolbar.setMovable(False)
        fit_action = QAction("Seite einpassen", self)
        fit_action.setShortcut("Ctrl+0")
        fit_action.triggered.connect(self._fit_page)
        zoom_out = QAction("−", self)
        zoom_out.setShortcut("Ctrl+-")
        zoom_out.triggered.connect(lambda: self.view.scale(0.85, 0.85))
        zoom_in = QAction("+", self)
        zoom_in.setShortcut("Ctrl++")
        zoom_in.triggered.connect(lambda: self.view.scale(1.15, 1.15))
        toolbar.addAction(fit_action)
        toolbar.addAction(zoom_out)
        toolbar.addAction(zoom_in)
        toolbar.addSeparator()
        undo_action = self.undo_stack.createUndoAction(self, "Rückgängig")
        assert undo_action is not None
        undo_action.setShortcut("Ctrl+Z")
        redo_action = self.undo_stack.createRedoAction(self, "Wiederholen")
        assert redo_action is not None
        redo_action.setShortcut("Ctrl+Y")
        toolbar.addAction(undo_action)
        toolbar.addAction(redo_action)
        delete_action = QAction("Feld löschen", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self._delete_selected)
        toolbar.addAction(delete_action)
        toolbar.addSeparator()
        add_button = QToolButton()
        add_button.setText("+ Feld hinzufügen")
        add_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        add_menu = add_button.menu()
        if add_menu is None:
            from PyQt6.QtWidgets import QMenu

            add_menu = QMenu(add_button)
            add_button.setMenu(add_menu)
        for field_type, label in (
            (TemplateFieldType.TEXT, "Textfeld"),
            (TemplateFieldType.MULTILINE, "Mehrzeiliges Textfeld"),
            (TemplateFieldType.DATE, "Datum"),
            (TemplateFieldType.CHECKBOX, "Kontrollkästchen"),
            (TemplateFieldType.RADIO, "Optionsfeld"),
            (TemplateFieldType.CHOICE, "Auswahlliste"),
            (TemplateFieldType.SIGNATURE_IMAGE, "Unterschriftsbild"),
            (TemplateFieldType.DIGITAL_SIGNATURE, "Digitales Signaturfeld"),
        ):
            action = QAction(label, add_menu)
            add_menu.addAction(action)
            action.setData(field_type.value)
            action.triggered.connect(
                lambda _checked=False, value=field_type: self._arm_field_type(value)
            )
        toolbar.addWidget(add_button)
        self.draw_hint = QLabel("  Ziehe anschließend das Feld auf der PDF-Seite auf.")
        toolbar.addWidget(self.draw_hint)
        toolbar.addSeparator()
        import_pdf24 = QAction("PDF24-Formular importieren", self)
        import_pdf24.triggered.connect(self._import_pdf24_spec)
        toolbar.addAction(import_pdf24)
        toolbar.addSeparator()
        previous_page = QAction("← Seite", self)
        previous_page.triggered.connect(self._previous_page)
        next_page = QAction("Seite →", self)
        next_page.triggered.connect(self._next_page)
        toolbar.addAction(previous_page)
        toolbar.addAction(next_page)
        self.page_label = QLabel()
        toolbar.addWidget(self.page_label)
        layout.addWidget(toolbar)

        metadata = QHBoxLayout()
        self.template_name = QLineEdit(
            self.existing_template.name if self.existing_template else self.analysis.title
        )
        self.template_id = QLineEdit(
            self.existing_template.id if self.existing_template else _slugify(self.analysis.title)
        )
        self.template_version = QLineEdit(
            self._next_version(self.existing_template.version)
            if self.existing_template
            else "1.0.0"
        )
        metadata.addWidget(QLabel("Name"))
        metadata.addWidget(self.template_name, 2)
        metadata.addWidget(QLabel("ID"))
        metadata.addWidget(self.template_id, 2)
        metadata.addWidget(QLabel("Version"))
        metadata.addWidget(self.template_version)
        layout.addLayout(metadata)

        splitter = QSplitter()
        splitter.setChildrenCollapsible(False)
        self.scene = QGraphicsScene(self)
        self.view = DesignerView(self.scene)
        self.view.rectangle_created.connect(self._create_field)
        self.view.field_selected.connect(self._select_field_id)
        self.pending_field_type = TemplateFieldType.TEXT

        field_panel = QWidget()
        field_layout = QVBoxLayout(field_panel)
        field_layout.addWidget(QLabel("<b>Felder auf der Seite</b>"))
        self.field_list = QListWidget()
        self.field_list.currentItemChanged.connect(self._select_from_list)
        field_layout.addWidget(self.field_list)
        delete_button = QPushButton("Ausgewähltes Feld löschen")
        delete_button.clicked.connect(self._delete_selected)
        field_layout.addWidget(delete_button)
        splitter.addWidget(field_panel)
        splitter.addWidget(self.view)

        side = QWidget()
        side_layout = QVBoxLayout(side)
        side_layout.addWidget(QLabel("<b>Eigenschaften</b>"))
        properties = QFormLayout()
        self.field_label = QLineEdit()
        self.field_label.editingFinished.connect(self._apply_properties)
        self.field_type = QComboBox()
        for field_type in TemplateFieldType:
            self.field_type.addItem(field_type.value, field_type.value)
        self.field_type.currentIndexChanged.connect(self._apply_properties)
        self.source_scope = QComboBox()
        self.source_scope.addItem("Profil – wiederverwendbare persönliche Daten", "profile")
        self.source_scope.addItem("Formular – Angabe nur für diese Vorlage", "form")
        self.source_scope.currentIndexChanged.connect(self._source_scope_changed)
        self.field_source = QComboBox()
        for source, label in sorted(SOURCE_LABELS.items(), key=lambda item: item[1]):
            self.field_source.addItem(label, source)
        self.field_source.currentIndexChanged.connect(self._apply_properties)
        self.form_source = QLineEdit()
        self.form_source.setPlaceholderText("z. B. absender_homepage")
        self.form_source.editingFinished.connect(self._apply_properties)
        self.default_value = QLineEdit()
        self.default_value.setPlaceholderText("Optionaler Vorgabewert")
        self.default_value.editingFinished.connect(self._apply_properties)
        self.font_family = QComboBox()
        for family in ("Helvetica", "Arial", "Times", "Courier"):
            self.font_family.addItem(family, family)
        self.font_family.currentIndexChanged.connect(self._apply_properties)
        self.font_size = QDoubleSpinBox()
        self.font_size.setRange(5.0, 36.0)
        self.font_size.setDecimals(1)
        self.font_size.setSuffix(" pt")
        self.font_size.editingFinished.connect(self._apply_properties)
        self.required = QCheckBox("Pflichtfeld")
        self.required.toggled.connect(self._apply_properties)
        self.x_position = self._coordinate_input()
        self.y_position = self._coordinate_input()
        self.field_width = self._coordinate_input(minimum=1.0)
        self.field_height = self._coordinate_input(minimum=1.0)
        for coordinate in (
            self.x_position,
            self.y_position,
            self.field_width,
            self.field_height,
        ):
            coordinate.editingFinished.connect(self._apply_coordinates)
        properties.addRow("Bezeichnung", self.field_label)
        properties.addRow("Feldtyp", self.field_type)
        properties.addRow("Datenquelle", self.source_scope)
        properties.addRow("Profilfeld", self.field_source)
        properties.addRow("Formularfeld", self.form_source)
        properties.addRow("Vorgabewert", self.default_value)
        properties.addRow("Schriftart", self.font_family)
        properties.addRow("Schriftgröße", self.font_size)
        properties.addRow("", self.required)
        properties.addRow("X-Position", self.x_position)
        properties.addRow("Y-Position", self.y_position)
        properties.addRow("Breite", self.field_width)
        properties.addRow("Höhe", self.field_height)
        side_layout.addLayout(properties)
        self.coordinates = QLabel("Kein Feld ausgewählt")
        self.coordinates.setWordWrap(True)
        side_layout.addWidget(self.coordinates)
        save_button = QPushButton("Templatepaket speichern und installieren")
        save_button.setObjectName("primary")
        save_button.clicked.connect(self._save_template)
        side_layout.addWidget(save_button)
        splitter.addWidget(side)
        splitter.setSizes([260, 900, 360])
        layout.addWidget(splitter)

    @staticmethod
    def _next_version(version: str) -> str:
        parts = version.split(".")
        if len(parts) == 3 and all(part.isdigit() for part in parts):
            return f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"
        return f"{version}.1"

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        super().resizeEvent(event)
        QTimer.singleShot(0, self._fit_page)

    @staticmethod
    def _coordinate_input(minimum: float = 0.0) -> QDoubleSpinBox:
        value = QDoubleSpinBox()
        value.setRange(minimum, 5000.0)
        value.setDecimals(1)
        value.setSingleStep(1.0)
        value.setSuffix(" pt")
        return value

    def _show_page(self, page_number: int) -> None:
        self.current_page = page_number
        samples, width, height = render_page(self.pdf_path, page_number, self.SCALE)
        image = QImage(samples, width, height, width * 3, QImage.Format.Format_RGB888).copy()
        self.scene.clear()
        self.items.clear()
        pixmap = QGraphicsPixmapItem(QPixmap.fromImage(image))
        pixmap.setZValue(-10)
        self.scene.addItem(pixmap)
        for field in self.fields:
            if field.page != page_number:
                continue
            scaled_field = DesignerField(
                field.id,
                field.label,
                field.type,
                field.page,
                Rect(
                    field.rect.x0 * self.SCALE,
                    field.rect.y0 * self.SCALE,
                    field.rect.x1 * self.SCALE,
                    field.rect.y1 * self.SCALE,
                ),
                field.source,
                field.required,
                field.option_value,
                field.default_value,
                field.font_family,
                field.font_size,
            )
            item = DesignerFieldItem(scaled_field, lambda field_id: self._item_moved(field_id))
            item.field = field
            item.setRect(0, 0, field.rect.width * self.SCALE, field.rect.height * self.SCALE)
            item.setPos(field.rect.x0 * self.SCALE, field.rect.y0 * self.SCALE)
            self.scene.addItem(item)
            self.items[field.id] = item
        self.scene.setSceneRect(0, 0, width, height)
        self.page_label.setText(f"Seite {page_number + 1} von {self.analysis.page_count}")
        self._fit_page()

    def _create_field(self, rectangle: QRectF) -> None:
        pdf_rect = Rect(
            rectangle.left() / self.SCALE,
            rectangle.top() / self.SCALE,
            rectangle.right() / self.SCALE,
            rectangle.bottom() / self.SCALE,
        )
        field = DesignerField(
            id=f"field-{uuid4().hex[:10]}",
            label="Neues Feld",
            type=self.pending_field_type,
            page=self.current_page,
            rect=pdf_rect,
        )
        self.undo_stack.push(AddFieldCommand(self, field))
        self.pending_field_type = TemplateFieldType.TEXT
        self.draw_hint.setText("  Feld angelegt. Auswählen, verschieben oder Eigenschaften ändern.")

    def _arm_field_type(self, field_type: TemplateFieldType) -> None:
        self.pending_field_type = field_type
        self.draw_hint.setText(
            f"  {self._field_type_label(field_type)}: Bereich auf der PDF-Seite aufziehen."
        )

    @staticmethod
    def _field_type_label(field_type: TemplateFieldType) -> str:
        return {
            TemplateFieldType.TEXT: "Textfeld",
            TemplateFieldType.MULTILINE: "Mehrzeiliges Textfeld",
            TemplateFieldType.DATE: "Datum",
            TemplateFieldType.CHECKBOX: "Kontrollkästchen",
            TemplateFieldType.RADIO: "Optionsfeld",
            TemplateFieldType.CHOICE: "Auswahlliste",
            TemplateFieldType.SIGNATURE_IMAGE: "Unterschriftsbild",
            TemplateFieldType.DIGITAL_SIGNATURE: "Digitales Signaturfeld",
        }[field_type]

    def insert_field(self, field: DesignerField) -> None:
        if all(existing.id != field.id for existing in self.fields):
            self.fields.append(field)
        self._refresh_list(field.id)
        self._show_page(self.current_page)

    def remove_field(self, field_id: str) -> None:
        self.fields = [field for field in self.fields if field.id != field_id]
        self._refresh_list()
        self._show_page(self.current_page)

    def _selected_field(self) -> DesignerField | None:
        item = self.field_list.currentItem()
        if item is None:
            return None
        field_id = str(item.data(Qt.ItemDataRole.UserRole))
        return next((field for field in self.fields if field.id == field_id), None)

    def _delete_selected(self) -> None:
        field = self._selected_field()
        if field is not None:
            self.undo_stack.push(DeleteFieldCommand(self, field))

    def _select_field_id(self, field_id: str) -> None:
        for index in range(self.field_list.count()):
            item = self.field_list.item(index)
            if item is not None and str(item.data(Qt.ItemDataRole.UserRole)) == field_id:
                self.field_list.setCurrentItem(item)
                return

    def _refresh_list(self, selected_id: str | None = None) -> None:
        current_id = selected_id
        current_item = self.field_list.currentItem()
        if current_id is None and current_item is not None:
            current_id = str(current_item.data(Qt.ItemDataRole.UserRole))
        self.field_list.clear()
        for field in sorted(self.fields, key=lambda item: (item.page, item.rect.y0)):
            item = QListWidgetItem(
                f"Seite {field.page + 1} · {field.label}\n"
                f"{field.type.value} → {field.source or 'Einmalfeld'}"
            )
            item.setData(Qt.ItemDataRole.UserRole, field.id)
            self.field_list.addItem(item)
            if field.id == current_id:
                self.field_list.setCurrentItem(item)

    def _select_from_list(
        self, current: QListWidgetItem | None, _previous: QListWidgetItem | None
    ) -> None:
        if current is None:
            return
        field = self._selected_field()
        if field is None:
            return
        if field.page != self.current_page:
            self._show_page(field.page)
        self.field_label.setText(field.label)
        type_index = self.field_type.findData(field.type.value)
        self.field_type.setCurrentIndex(max(0, type_index))
        source_index = self.field_source.findData(field.source)
        is_form = field.source.startswith("form.") or not field.source
        scope_index = self.source_scope.findData("form" if is_form else "profile")
        self.source_scope.setCurrentIndex(max(0, scope_index))
        self.field_source.setCurrentIndex(max(0, source_index))
        self.form_source.setText(field.source.removeprefix("form.") if is_form else "")
        self.default_value.setText(field.default_value)
        font_index = self.font_family.findData(field.font_family)
        self.font_family.setCurrentIndex(max(0, font_index))
        self.font_size.setValue(field.font_size)
        self._source_scope_changed()
        self.required.setChecked(field.required)
        self.x_position.setValue(field.rect.x0)
        self.y_position.setValue(field.rect.y0)
        self.field_width.setValue(field.rect.width)
        self.field_height.setValue(field.rect.height)
        self._show_coordinates(field)
        graphics_item = self.items.get(field.id)
        if graphics_item:
            graphics_item.setSelected(True)
            graphics_item.setFocus()
            self.view.centerOn(graphics_item)

    def _apply_properties(self) -> None:
        field = self._selected_field()
        if field is None:
            return
        field.label = self.field_label.text().strip() or "Unbenanntes Feld"
        field.type = TemplateFieldType(str(self.field_type.currentData()))
        if self.source_scope.currentData() == "form":
            key = _slugify(self.form_source.text() or field.label).replace("-", "_")
            field.source = f"form.{key}"
        else:
            field.source = str(self.field_source.currentData() or "")
        field.default_value = self.default_value.text()
        field.font_family = str(self.font_family.currentData() or "Helvetica")
        field.font_size = self.font_size.value()
        field.required = self.required.isChecked()
        self._refresh_list(field.id)

    def _source_scope_changed(self) -> None:
        is_form = self.source_scope.currentData() == "form"
        self.field_source.setVisible(not is_form)
        self.form_source.setVisible(is_form)

    def _apply_coordinates(self) -> None:
        field = self._selected_field()
        if field is None:
            return
        field.rect = Rect(
            self.x_position.value(),
            self.y_position.value(),
            self.x_position.value() + self.field_width.value(),
            self.y_position.value() + self.field_height.value(),
        )
        self._show_page(self.current_page)
        self._refresh_list(field.id)

    def _item_moved(self, field_id: str) -> None:
        item = self.items.get(field_id)
        field = next((entry for entry in self.fields if entry.id == field_id), None)
        if item is None or field is None:
            return
        position = item.pos()
        field.rect = Rect(
            position.x() / self.SCALE,
            position.y() / self.SCALE,
            (position.x() + item.rect().width()) / self.SCALE,
            (position.y() + item.rect().height()) / self.SCALE,
        )
        self.x_position.setValue(field.rect.x0)
        self.y_position.setValue(field.rect.y0)
        self.field_width.setValue(field.rect.width)
        self.field_height.setValue(field.rect.height)
        self._show_coordinates(field)

    def _show_coordinates(self, field: DesignerField) -> None:
        self.coordinates.setText(
            f"x={field.rect.x0:.1f}, y={field.rect.y0:.1f}, "
            f"Breite={field.rect.width:.1f}, Höhe={field.rect.height:.1f} PDF-Punkte\n"
            "Pfeiltasten: 1 Punkt · Umschalt+Pfeil: 10 Punkte"
        )

    def _previous_page(self) -> None:
        if self.current_page > 0:
            self._show_page(self.current_page - 1)

    def _next_page(self) -> None:
        if self.current_page + 1 < self.analysis.page_count:
            self._show_page(self.current_page + 1)

    def _fit_page(self) -> None:
        if not hasattr(self, "view") or self.scene.sceneRect().isEmpty():
            return
        self.view.resetTransform()
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def _import_pdf24_spec(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "PDF24-Formular importieren",
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
        if self.fields:
            choice = QMessageBox.question(
                self,
                "Erkannte Felder ersetzen?",
                f"PDF24 enthält {len(imported)} Felder.\n\n"
                "Sollen die aktuell erkannten Felder dadurch ersetzt werden?",
            )
            if choice != QMessageBox.StandardButton.Yes:
                return
        self.fields = [
            DesignerField(
                id=str(item["id"]),
                label=str(item["label"]),
                type=item["type"],
                page=int(item["page"]),
                rect=item["rect"],
                required=bool(item["required"]),
            )
            for item in imported
        ]
        self._refresh_list()
        self._show_page(0)
        QMessageBox.information(
            self,
            "PDF24-Formular importiert",
            f"{len(self.fields)} Felder wurden übernommen.\n\n"
            "Bitte ordne rechts die passenden Profil- oder Einmalfelder zu.",
        )

    def _save_template(self) -> None:
        template_id = _slugify(self.template_id.text())
        template = Template(
            id=template_id,
            name=self.template_name.text().strip(),
            version=self.template_version.text().strip(),
            language="de",
            status=TemplateStatus.LOCAL,
            minimum_app_version="0.7.0",
            source_pdf=self.pdf_path.name,
            fields=[
                TemplateField(
                    field.id,
                    field.label,
                    field.type,
                    field.page,
                    field.rect,
                    field.source,
                    field.required,
                    field.option_value,
                    field.default_value,
                    field.font_family,
                    field.font_size,
                )
                for field in self.fields
            ],
        )
        errors = template.validate()
        if errors:
            QMessageBox.warning(self, "Template unvollständig", "\n".join(errors.values()))
            return
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Templatepaket speichern",
            f"{template.id}-{template.version}.psfstemplate",
            "PDF SmartForms Template (*.psfstemplate)",
        )
        if not filename:
            return
        try:
            target = build_template_package(template, self.pdf_path, Path(filename))
            self.repository.install_package(target)
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "Template konnte nicht gespeichert werden", str(error))
            return
        QMessageBox.information(
            self,
            "Template gespeichert",
            "Das Paket wurde geprüft, gespeichert und lokal installiert.",
        )
        self.accept()


def _slugify(value: str) -> str:
    return _SLUG.sub("-", value.casefold()).strip("-") or "local.template"
