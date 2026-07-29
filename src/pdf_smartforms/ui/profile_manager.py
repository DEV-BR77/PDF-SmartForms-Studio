"""Profile management dialog."""

from __future__ import annotations

from copy import deepcopy

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pdf_smartforms.domain.profiles import Profile
from pdf_smartforms.profiles.repository import ProfileRepository
from pdf_smartforms.ui.profile_editor import ProfileEditorDialog


class ProfileManagerDialog(QDialog):
    """List and manage profiles without exposing storage details."""

    def __init__(self, repository: ProfileRepository, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.repository = repository
        self.profiles: list[Profile] = []
        self.setWindowTitle("Profile verwalten")
        self.resize(820, 520)
        layout = QVBoxLayout(self)
        heading = QLabel("Profile")
        heading.setObjectName("title")
        layout.addWidget(heading)
        description = QLabel(
            "Profile enthalten wiederverwendbare Stammdaten. "
            "Formularbezogene Einmalfelder werden später nicht automatisch gespeichert."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Profil", "Teilnehmende Person", "Ort", "E-Mail", "Zusatzfelder"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._edit_profile)
        layout.addWidget(self.table)
        actions = QHBoxLayout()
        create = QPushButton("Neues Profil")
        create.setObjectName("primary")
        create.clicked.connect(self._create_profile)
        edit = QPushButton("Profil bearbeiten")
        edit.clicked.connect(self._edit_profile)
        delete = QPushButton("Profil löschen")
        delete.clicked.connect(self._delete_profile)
        actions.addWidget(create)
        actions.addWidget(edit)
        actions.addWidget(delete)
        actions.addStretch()
        layout.addLayout(actions)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._reload()

    def _reload(self) -> None:
        self.profiles = self.repository.list()
        self.table.setRowCount(len(self.profiles))
        for row, profile in enumerate(self.profiles):
            participant = (
                f"{profile.participant_first_name} {profile.participant_last_name}".strip()
            )
            values = (
                profile.effective_display_name(),
                participant,
                profile.city,
                profile.email,
                str(len(profile.custom_fields)),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, profile.id)
                self.table.setItem(row, column, item)
        self.table.resizeColumnsToContents()

    def _selected_profile(self) -> Profile | None:
        row = self.table.currentRow()
        return self.profiles[row] if 0 <= row < len(self.profiles) else None

    def _create_profile(self) -> None:
        editor = ProfileEditorDialog(parent=self)
        if editor.exec() == QDialog.DialogCode.Accepted:
            self.repository.save(editor.profile)
            self._reload()

    def _edit_profile(self) -> None:
        profile = self._selected_profile()
        if profile is None:
            QMessageBox.information(self, "Profil auswählen", "Bitte zuerst ein Profil auswählen.")
            return
        editor = ProfileEditorDialog(deepcopy(profile), self)
        if editor.exec() == QDialog.DialogCode.Accepted:
            self.repository.save(editor.profile)
            self._reload()

    def _delete_profile(self) -> None:
        profile = self._selected_profile()
        if profile is None:
            QMessageBox.information(self, "Profil auswählen", "Bitte zuerst ein Profil auswählen.")
            return
        answer = QMessageBox.question(
            self,
            "Profil wirklich löschen?",
            f"„{profile.effective_display_name()}“ wird dauerhaft gelöscht.\n\n"
            "Vorhandene exportierte PDFs bleiben unverändert.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.repository.delete(profile.id)
            self._reload()
