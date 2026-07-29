"""Distribution-list and exchange-package UI."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pdf_smartforms.distribution.exchange_package import build_exchange_package
from pdf_smartforms.distribution.repository import DistributionListRepository
from pdf_smartforms.domain.distribution import DistributionList


class DistributionManagerDialog(QDialog):
    """Manage local recipient lists and create privacy-safe exchange packages."""

    def __init__(
        self,
        repository: DistributionListRepository,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.repository = repository
        self.lists: list[DistributionList] = []
        self.setWindowTitle("Verteilerlisten und Austauschpakete")
        self.resize(760, 500)
        layout = QVBoxLayout(self)
        heading = QLabel("Verteilerlisten")
        heading.setObjectName("title")
        layout.addWidget(heading)
        notice = QLabel(
            "Die Anwendung versendet nichts automatisch. Verteilerlisten bleiben lokal. "
            "Austauschpakete enthalten ein bewusst leeres Profil und keine Unterschriften."
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Liste", "Empfänger"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        actions = QHBoxLayout()
        new_button = QPushButton("Neue Liste")
        new_button.setObjectName("primary")
        new_button.clicked.connect(self._new_list)
        edit_button = QPushButton("Liste bearbeiten")
        edit_button.clicked.connect(self._edit_list)
        delete_button = QPushButton("Liste löschen")
        delete_button.clicked.connect(self._delete_list)
        package_button = QPushButton("Austauschpaket erstellen")
        package_button.clicked.connect(self._create_package)
        for button in (new_button, edit_button, delete_button, package_button):
            actions.addWidget(button)
        layout.addLayout(actions)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._reload()

    def _reload(self) -> None:
        self.lists = self.repository.list()
        self.table.setRowCount(len(self.lists))
        for row, item in enumerate(self.lists):
            self.table.setItem(row, 0, QTableWidgetItem(item.name))
            self.table.setItem(row, 1, QTableWidgetItem(str(len(item.recipients))))
        self.table.resizeColumnsToContents()

    def _selected(self) -> DistributionList | None:
        row = self.table.currentRow()
        return self.lists[row] if 0 <= row < len(self.lists) else None

    def _new_list(self) -> None:
        self._edit(DistributionList())

    def _edit_list(self) -> None:
        selected = self._selected()
        if selected is None:
            QMessageBox.information(self, "Liste auswählen", "Bitte zuerst eine Liste auswählen.")
            return
        self._edit(selected)

    def _edit(self, distribution_list: DistributionList) -> None:
        name, accepted = QInputDialog.getText(
            self, "Verteilerliste", "Name:", text=distribution_list.name
        )
        if not accepted:
            return
        recipients, accepted = QInputDialog.getMultiLineText(
            self,
            "Empfänger",
            "Eine E-Mail-Adresse pro Zeile:",
            "\n".join(distribution_list.recipients),
        )
        if not accepted:
            return
        distribution_list.name = name.strip()
        distribution_list.recipients = [
            line.strip() for line in recipients.splitlines() if line.strip()
        ]
        try:
            self.repository.save(distribution_list)
        except ValueError as error:
            QMessageBox.warning(self, "Liste ungültig", str(error))
            return
        self._reload()

    def _delete_list(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        answer = QMessageBox.question(
            self,
            "Liste löschen?",
            f"„{selected.name}“ wird dauerhaft gelöscht.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.repository.delete(selected.id)
            self._reload()

    def _create_package(self) -> None:
        pdf, _ = QFileDialog.getOpenFileName(self, "PDF auswählen", "", "PDF-Dokumente (*.pdf)")
        if not pdf:
            return
        template, _ = QFileDialog.getOpenFileName(
            self,
            "Optionales Grundtemplate auswählen",
            "",
            "PDF SmartForms Template (*.psfstemplate);;Ohne Template (*)",
        )
        target, _ = QFileDialog.getSaveFileName(
            self,
            "Austauschpaket speichern",
            f"{Path(pdf).stem}.psfspackage",
            "PDF SmartForms Paket (*.psfspackage)",
        )
        if not target:
            return
        try:
            build_exchange_package(
                Path(target),
                pdf=Path(pdf),
                template_package=Path(template) if template else None,
            )
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "Paket konnte nicht erstellt werden", str(error))
            return
        QMessageBox.information(
            self,
            "Austauschpaket erstellt",
            "Enthalten sind PDF, leeres Profil, Anleitung, Prüfsummen und optional "
            "das Grundtemplate. Keine Unterschriften oder persönlichen Werte.",
        )
