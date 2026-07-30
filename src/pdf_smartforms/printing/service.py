"""Print PDF pages through Qt without relying on a Windows file association."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pymupdf
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
from PyQt6.QtWidgets import QDialog, QWidget


class PdfPrintError(RuntimeError):
    """The selected PDF could not be rendered or sent to the printer."""


def print_pdf(path: Path, parent: QWidget | None = None) -> bool:
    """Show the system print dialog and render every page to the chosen printer."""
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    dialog = QPrintDialog(printer, parent)
    dialog.setWindowTitle("PDF drucken")
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return False
    try:
        document: Any = pymupdf.open(path)  # type: ignore[no-untyped-call]
    except (OSError, RuntimeError, pymupdf.FileDataError) as error:
        raise PdfPrintError("Die Druckdatei konnte nicht geöffnet werden.") from error
    painter = QPainter()
    try:
        if not painter.begin(printer):
            raise PdfPrintError("Der ausgewählte Drucker konnte nicht gestartet werden.")
        with document:
            for page_number in range(document.page_count):
                page: Any = document.load_page(page_number)
                render_dpi = min(200, max(96, printer.resolution()))
                matrix = pymupdf.Matrix(render_dpi / 72, render_dpi / 72)  # type: ignore
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                image = QImage(
                    pixmap.samples,
                    pixmap.width,
                    pixmap.height,
                    pixmap.stride,
                    QImage.Format.Format_RGB888,
                ).copy()
                target = _fit_page(
                    QRectF(printer.pageRect(QPrinter.Unit.DevicePixel)),
                    image.width(),
                    image.height(),
                )
                painter.drawImage(target, image)
                if page_number + 1 < document.page_count and not printer.newPage():
                    raise PdfPrintError("Eine weitere Druckseite konnte nicht angelegt werden.")
    finally:
        if painter.isActive():
            painter.end()
    return True


def _fit_page(area: QRectF, width: int, height: int) -> QRectF:
    scale = min(area.width() / width, area.height() / height)
    target_width = width * scale
    target_height = height * scale
    return QRectF(
        area.x() + (area.width() - target_width) / 2,
        area.y() + (area.height() - target_height) / 2,
        target_width,
        target_height,
    )
