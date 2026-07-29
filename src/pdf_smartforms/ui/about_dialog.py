"""About and build information dialog."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QPushButton, QVBoxLayout

from pdf_smartforms.build_info import APP_NAME, COPYRIGHT, current_build_info


class AboutDialog(QDialog):
    """Display the exact version users should include in support requests."""

    def __init__(self, parent: object | None = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        info = current_build_info()
        self.setWindowTitle(f"Über {APP_NAME}")
        self.setMinimumWidth(460)
        layout = QVBoxLayout(self)
        title = QLabel(APP_NAME)
        title.setObjectName("title")
        layout.addWidget(title)
        details = QLabel(
            f"Version: {info.version}<br>"
            f"Edition: {info.edition}<br>"
            f"Build: {info.build}<br>"
            f"Commit: {info.commit}<br><br>"
            f"{COPYRIGHT}<br><br>"
            "Lokale Verarbeitung · keine Telemetrie · kein automatischer Versand"
        )
        details.setTextFormat(Qt.TextFormat.RichText)
        details.setWordWrap(True)
        layout.addWidget(details)
        repository = QPushButton("Privates Repository öffnen")
        repository.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(info.repository_url)))
        layout.addWidget(repository)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
