"""Main application window."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeyEvent
from PyQt6.QtWidgets import (
    QFileDialog,
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
from pdf_smartforms.distribution.exchange_package import (
    UnsafeExchangePackage,
    import_exchange_package,
)
from pdf_smartforms.distribution.repository import DistributionListRepository
from pdf_smartforms.field_dictionary.repository import FieldDictionaryRepository
from pdf_smartforms.infrastructure.paths import AppPaths
from pdf_smartforms.profiles.repository import ProfileRepository
from pdf_smartforms.signatures.repository import SignatureRepository
from pdf_smartforms.templates.repository import TemplateRepository
from pdf_smartforms.ui.about_dialog import AboutDialog
from pdf_smartforms.ui.backup_manager import BackupManagerDialog
from pdf_smartforms.ui.distribution_manager import DistributionManagerDialog
from pdf_smartforms.ui.pdf_analysis_dialog import PdfAnalysisDialog
from pdf_smartforms.ui.profile_manager import ProfileManagerDialog
from pdf_smartforms.ui.signature_manager import SignatureManagerDialog
from pdf_smartforms.ui.template_designer import TemplateDesignerDialog
from pdf_smartforms.ui.template_manager import TemplateManagerDialog


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
        self.profile_repository = ProfileRepository(paths.profiles)
        self.template_repository = TemplateRepository(paths.templates)
        self.dictionary_repository = FieldDictionaryRepository(paths.field_dictionary)
        self.signature_repository = SignatureRepository(paths.signatures)
        self.distribution_repository = DistributionListRepository(paths.distribution_lists)
        self.setWindowTitle(f"{APP_NAME} · {__version__}")
        self.resize(980, 640)
        self.setMinimumSize(760, 520)
        page = WelcomePage()
        page.own_pdf_requested.connect(self._select_pdf)
        page.package_requested.connect(self._import_received_package)
        self.setCentralWidget(page)
        self._build_menu()
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)
        status_bar.showMessage("Bereit · lokale Verarbeitung")

    def _build_menu(self) -> None:
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)
        profile_menu = QMenu("&Profile", menu_bar)
        menu_bar.addMenu(profile_menu)
        manage_profiles = QAction("Profile verwalten", profile_menu)
        manage_profiles.setShortcut("Ctrl+P")
        manage_profiles.setShortcutVisibleInContextMenu(False)
        manage_profiles.triggered.connect(self._show_profiles)
        profile_menu.addAction(manage_profiles)
        template_menu = QMenu("&Templates", menu_bar)
        menu_bar.addMenu(template_menu)
        manage_templates = QAction("Templates verwalten", template_menu)
        manage_templates.setShortcut("Ctrl+T")
        manage_templates.setShortcutVisibleInContextMenu(False)
        manage_templates.triggered.connect(self._show_templates)
        template_menu.addAction(manage_templates)
        create_template = QAction("Neues Template aus PDF", template_menu)
        create_template.setShortcut("Ctrl+Shift+T")
        create_template.setShortcutVisibleInContextMenu(False)
        create_template.triggered.connect(self._create_template)
        template_menu.addAction(create_template)
        signature_menu = QMenu("&Unterschriften", menu_bar)
        menu_bar.addMenu(signature_menu)
        manage_signatures = QAction("Unterschriften verwalten", signature_menu)
        manage_signatures.setShortcut("Ctrl+U")
        manage_signatures.setShortcutVisibleInContextMenu(False)
        manage_signatures.triggered.connect(self._show_signatures)
        signature_menu.addAction(manage_signatures)
        distribution_menu = QMenu("&Verteilen", menu_bar)
        menu_bar.addMenu(distribution_menu)
        manage_distribution = QAction("Verteilerlisten und Austauschpakete", distribution_menu)
        manage_distribution.triggered.connect(self._show_distribution)
        distribution_menu.addAction(manage_distribution)
        data_menu = QMenu("&Daten", menu_bar)
        menu_bar.addMenu(data_menu)
        backup_action = QAction("Datensicherung und Wiederherstellung", data_menu)
        backup_action.setShortcut("Ctrl+Shift+B")
        backup_action.setShortcutVisibleInContextMenu(False)
        backup_action.triggered.connect(self._show_backup_manager)
        data_menu.addAction(backup_action)
        help_menu = QMenu("&Hilfe", menu_bar)
        menu_bar.addMenu(help_menu)
        about_action = QAction(f"Über {APP_NAME}", help_menu)
        help_menu.addAction(about_action)
        about_action.triggered.connect(self._show_about)

    def _show_profiles(self) -> None:
        ProfileManagerDialog(self.profile_repository, self).exec()

    def _show_templates(self) -> None:
        TemplateManagerDialog(self.template_repository, self).exec()

    def _create_template(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "PDF für neues Template auswählen",
            "",
            "PDF-Dokumente (*.pdf)",
        )
        if filename:
            try:
                TemplateDesignerDialog(Path(filename), self.template_repository, self).exec()
            except ValueError as error:
                QMessageBox.critical(self, "Template-Designer konnte nicht starten", str(error))

    def _show_signatures(self) -> None:
        SignatureManagerDialog(self.signature_repository, self).exec()

    def _show_distribution(self) -> None:
        DistributionManagerDialog(self.distribution_repository, self).exec()

    def _show_backup_manager(self) -> None:
        BackupManagerDialog(self.paths, self).exec()

    def _select_pdf(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "PDF auswählen",
            "",
            "PDF-Dokumente (*.pdf)",
        )
        if not filename:
            return
        try:
            PdfAnalysisDialog(
                Path(filename),
                self.dictionary_repository,
                self.signature_repository,
                self.profile_repository,
                self,
            ).exec()
        except ValueError as error:
            QMessageBox.critical(self, "PDF konnte nicht analysiert werden", str(error))

    def _import_received_package(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Erhaltenes Formularpaket auswählen",
            "",
            "PDF SmartForms Paket (*.psfspackage *.zip)",
        )
        if not filename:
            return
        try:
            imported = import_exchange_package(
                Path(filename), self.paths.generated_documents / "received-packages"
            )
        except (OSError, UnsafeExchangePackage, ValueError) as error:
            QMessageBox.critical(self, "Paketimport blockiert", str(error))
            return
        pdfs = list(imported.glob("*.pdf"))
        QMessageBox.information(
            self,
            "Paket sicher importiert",
            "Prüfsummen und Inhalte wurden geprüft. Das enthaltene Profil ist leer "
            "und kann mit eigenen Angaben ergänzt werden.",
        )
        if len(pdfs) == 1:
            PdfAnalysisDialog(
                pdfs[0],
                self.dictionary_repository,
                self.signature_repository,
                self.profile_repository,
                self,
            ).exec()

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
