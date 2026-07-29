"""Visual PDF analysis with accessible field states."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QImage, QPen, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from pdf_smartforms.domain.detection import DetectedField, MatchStatus
from pdf_smartforms.pdf.analyzer import analyze_pdf, render_page

_COLORS = {
    MatchStatus.MAPPED: QColor("#1f9d55"),
    MatchStatus.UNCERTAIN: QColor("#d79614"),
    MatchStatus.MISSING: QColor("#d33c3c"),
}


class PdfAnalysisDialog(QDialog):
    """Display a rendered PDF with non-printing field overlays."""

    SCALE = 1.5

    def __init__(self, pdf_path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.analysis = analyze_pdf(pdf_path)
        self.current_page = 0
        self.overlay_items: dict[str, QGraphicsRectItem] = {}
        self.setWindowTitle(f"PDF analysieren · {self.analysis.title}")
        self.resize(1180, 760)
        self._build_ui()
        self._populate_field_list()
        self._show_page(0)
        if self.analysis.warnings:
            QMessageBox.information(self, "Analysehinweis", "\n".join(self.analysis.warnings))

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        title = QLabel(self.analysis.title)
        title.setObjectName("title")
        top.addWidget(title)
        top.addStretch()
        zoom_out = QPushButton("−")
        zoom_out.setAccessibleName("Vorschau verkleinern")
        zoom_out.clicked.connect(lambda: self.view.scale(1 / 1.15, 1 / 1.15))
        zoom_in = QPushButton("+")
        zoom_in.setAccessibleName("Vorschau vergrößern")
        zoom_in.clicked.connect(lambda: self.view.scale(1.15, 1.15))
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
            self.previous_button,
            self.page_label,
            self.next_button,
        ):
            top.addWidget(widget)
        layout.addLayout(top)

        splitter = QSplitter()
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        splitter.addWidget(self.view)
        side = QWidget()
        side_layout = QVBoxLayout(side)
        side_layout.addWidget(QLabel("Erkannte Felder"))
        legend = QLabel(
            "✓ Grün: zugeordnet\n" "⚠ Gelb: Prüfung erforderlich\n" "✕ Rot: nicht zugeordnet"
        )
        side_layout.addWidget(legend)
        self.field_list = QListWidget()
        self.field_list.currentItemChanged.connect(self._focus_selected_field)
        side_layout.addWidget(self.field_list)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        side_layout.addWidget(self.summary)
        splitter.addWidget(side)
        splitter.setSizes([820, 320])
        layout.addWidget(splitter)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate_field_list(self) -> None:
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
        self.scene.setSceneRect(0, 0, width, height)
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
        if field.page != self.current_page:
            self._show_page(field.page)
        overlay = self.overlay_items.get(field.id)
        if overlay is not None:
            self.view.centerOn(overlay)
            overlay.setPen(QPen(_COLORS[field.status], 6))

    def _previous_page(self) -> None:
        if self.current_page > 0:
            self._show_page(self.current_page - 1)

    def _next_page(self) -> None:
        if self.current_page + 1 < self.analysis.page_count:
            self._show_page(self.current_page + 1)
