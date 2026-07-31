"""Template management UI."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pdf_smartforms.domain.templates import Template, TemplateStatus
from pdf_smartforms.templates.package_importer import (
    UnsafeTemplatePackage,
    inspect_package,
)
from pdf_smartforms.templates.repository import TemplateRepository

_STATUS_LABELS = {
    TemplateStatus.VERIFIED: "✓ Verifiziert",
    TemplateStatus.COMMUNITY: "⚠ Community",
    TemplateStatus.EXPERIMENTAL: "◌ Experimentell",
    TemplateStatus.LOCAL: "● Lokal",
}


class TemplateManagerDialog(QDialog):
    """Show installed templates and import validated packages."""

    def __init__(self, repository: TemplateRepository, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.repository = repository
        self.templates: list[Template] = []
        self.setWindowTitle("Templates verwalten")
        self.resize(860, 520)
        layout = QVBoxLayout(self)
        heading = QLabel("Templates")
        heading.setObjectName("title")
        layout.addWidget(heading)
        description = QLabel(
            "Unbekannte und Community-Templates werden nie automatisch als "
            "vertrauenswürdig behandelt. Der Import prüft Pfade, Dateitypen und Größen."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            [
                "Name",
                "Version",
                "Erstellt am",
                "Status",
                "Sprache",
                "Felder",
                "Min. App-Version",
            ]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        actions = QHBoxLayout()
        import_button = QPushButton("Templatepaket importieren")
        import_button.setObjectName("primary")
        import_button.clicked.connect(self._import_package)
        edit_button = QPushButton("Template bearbeiten")
        edit_button.clicked.connect(self._edit_template)
        delete_button = QPushButton("Template entfernen")
        delete_button.clicked.connect(self._delete_template)
        actions.addWidget(import_button)
        actions.addWidget(edit_button)
        actions.addWidget(delete_button)
        actions.addStretch()
        layout.addLayout(actions)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._reload()

    def _reload(self) -> None:
        self.templates = self.repository.list()
        self.table.setRowCount(len(self.templates))
        for row, template in enumerate(self.templates):
            values = (
                template.name,
                template.version,
                self.repository.created_date(template),
                _STATUS_LABELS[template.status],
                template.language,
                str(len(template.fields)),
                template.minimum_app_version,
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, template.id)
                self.table.setItem(row, column, item)
        self.table.resizeColumnsToContents()

    def _edit_template(self) -> None:
        template = self._selected_template()
        if template is None:
            QMessageBox.information(
                self, "Template auswählen", "Bitte zuerst ein Template auswählen."
            )
            return
        source_pdf = self.repository.source_pdf_path(template)
        if source_pdf is None:
            QMessageBox.information(
                self,
                "PDF nicht enthalten",
                "Dieses Template enthält kein bearbeitbares Quell-PDF.",
            )
            return
        from pdf_smartforms.ui.template_designer import TemplateDesignerDialog

        if TemplateDesignerDialog(
            source_pdf,
            self.repository,
            self,
            existing_template=template,
        ).exec():
            self._reload()

    def _selected_template(self) -> Template | None:
        row = self.table.currentRow()
        return self.templates[row] if 0 <= row < len(self.templates) else None

    def _import_package(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Templatepaket auswählen",
            "",
            "PDF SmartForms Template (*.psfstemplate *.zip)",
        )
        if not filename:
            return
        path = Path(filename)
        try:
            inspected = inspect_package(path)
        except (UnsafeTemplatePackage, OSError, ValueError) as error:
            QMessageBox.critical(self, "Import blockiert", str(error))
            return
        checksum_status = (
            "Prüfsummen wurden erfolgreich bestätigt."
            if inspected.checksums_verified
            else "Das Paket enthält keine Prüfsummen."
        )
        answer = QMessageBox.question(
            self,
            "Template importieren?",
            f"Name: {inspected.template.name}\n"
            f"Version: {inspected.template.version}\n"
            f"Status: {_STATUS_LABELS[inspected.template.status]}\n"
            f"Dateien: {len(inspected.files)}\n\n"
            f"{checksum_status}\n\n"
            "Community- und unbekannte Inhalte vor Verwendung visuell prüfen.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.repository.install_package(path)
        except (UnsafeTemplatePackage, OSError, ValueError) as error:
            QMessageBox.critical(self, "Import fehlgeschlagen", str(error))
            return
        self._reload()

    def _delete_template(self) -> None:
        template = self._selected_template()
        if template is None:
            QMessageBox.information(
                self, "Template auswählen", "Bitte zuerst ein Template auswählen."
            )
            return
        answer = QMessageBox.question(
            self,
            "Template entfernen?",
            f"„{template.name}“ Version {template.version} wird lokal entfernt.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.repository.delete(template)
            self._reload()
