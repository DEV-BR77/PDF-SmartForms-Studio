"""Composition root."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from PyQt6.QtWidgets import QApplication

from pdf_smartforms.infrastructure.logging import configure_logging
from pdf_smartforms.infrastructure.paths import AppPaths, create_app_paths
from pdf_smartforms.infrastructure.temporary import clean_temporary_root
from pdf_smartforms.ui.main_window import MainWindow
from pdf_smartforms.ui.theme import application_stylesheet


@dataclass(slots=True)
class DesktopRuntime:
    """Owns resources needed for one GUI process."""

    paths: AppPaths

    def run(self, arguments: Sequence[str]) -> int:
        app = QApplication(list(arguments))
        app.setApplicationName("PDF SmartForms Studio")
        app.setOrganizationName("Björn Radke")
        app.setStyleSheet(application_stylesheet())
        window = MainWindow(self.paths)
        window.show()
        return app.exec()


def build_runtime() -> DesktopRuntime:
    """Create folders and logging before the UI starts."""
    paths = create_app_paths()
    clean_temporary_root(paths.temporary)
    configure_logging(paths.logs)
    return DesktopRuntime(paths=paths)
