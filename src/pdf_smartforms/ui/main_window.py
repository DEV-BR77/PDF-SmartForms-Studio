"""Main application window."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeyEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from pdf_smartforms.build_info import APP_NAME, __version__
from pdf_smartforms.infrastructure.paths import AppPaths
from pdf_smartforms.ui.about_dialog import AboutDialog


class WelcomePage(QWidget):
    """First-run choice requested by the product specification."""

    own_pdf_requested = pyqtSignal()
    package_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(48, 42, 48, 42)
        outer.addStretch()
        card = QFrame()
        card.setObjectName("hero")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 36, 40, 36)
        card_layout.setSpacing(16)
        eyebrow = QLabel("SICHER · LOKAL · MODULAR")
        eyebrow.setObjectName("eyebrow")
        card_layout.addWidget(eyebrow)
        title = QLabel(APP_NAME)
        title.setObjectName("title")
        card_layout.addWidget(title)
        subtitle = QLabel(
            "Wie möchtest du beginnen? Deine Dokumente und Profildaten "
            "bleiben standardmäßig auf diesem Computer."
        )
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        card_layout.addWidget(subtitle)
        actions = QHBoxLayout()
        own_pdf = QPushButton("Eigenes PDF bearbeiten")
        own_pdf.setObjectName("primary")
        own_pdf.setAccessibleName("Eigenes PDF bearbeiten")
        own_pdf.clicked.connect(self.own_pdf_requested)
        package = QPushButton("Erhaltenes Paket importieren")
        package.setAccessibleName("Erhaltenes Formularpaket importieren")
        package.clicked.connect(self.package_requested)
        actions.addWidget(own_pdf)
        actions.addWidget(package)
        card_layout.addLayout(actions)
        privacy = QLabel(
            "Es wird nichts automatisch versendet. Vor Export oder E-Mail "
            "erscheint später immer eine Sicherheitsvorschau."
        )
        privacy.setWordWrap(True)
        privacy.setStyleSheet("color: #687386; margin-top: 8px;")
        card_layout.addWidget(privacy)
        outer.addWidget(card)
        outer.addStretch()


class MainWindow(QMainWindow):
    """Application shell for the foundation milestone."""

    def __init__(self, paths: AppPaths) -> None:
        super().__init__()
        self.paths = paths
        self.setWindowTitle(f"{APP_NAME} · {__version__}")
        self.resize(980, 640)
        self.setMinimumSize(760, 520)
        page = WelcomePage()
        page.own_pdf_requested.connect(lambda: self._not_yet_available("PDF-Import", "PSFS-040"))
        page.package_requested.connect(lambda: self._not_yet_available("Paketimport", "PSFS-086"))
        self.setCentralWidget(page)
        self._build_menu()
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)
        status_bar.showMessage("Bereit · lokale Verarbeitung")

    def _build_menu(self) -> None:
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)
        help_menu = QMenu("&Hilfe", menu_bar)
        menu_bar.addMenu(help_menu)
        about_action = QAction(f"Über {APP_NAME}", help_menu)
        help_menu.addAction(about_action)
        about_action.triggered.connect(self._show_about)

    def _show_about(self) -> None:
        AboutDialog(self).exec()

    def _not_yet_available(self, feature: str, task: str) -> None:
        QMessageBox.information(
            self,
            f"{feature} ist vorbereitet",
            f"Diese Funktion wird in Aufgabe {task} implementiert.\n\n"
            "Die Foundation-Version prüft zunächst Oberfläche, lokale "
            "Datenspeicherung, Datenschutz und Build-Prozess.",
            QMessageBox.StandardButton.Ok,
        )

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if event is not None and event.key() == Qt.Key.Key_F1:
            self._show_about()
            return
        super().keyPressEvent(event)
