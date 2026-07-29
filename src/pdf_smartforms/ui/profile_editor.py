"""Profile editor dialog."""

from __future__ import annotations

import re
from datetime import date

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pdf_smartforms.domain.profiles import (
    CustomField,
    FieldSensitivity,
    Guardian,
    Profile,
)

_KEY_SANITIZER = re.compile(r"[^a-z0-9_]+")


class ProfileEditorDialog(QDialog):
    """Create or edit a flexible profile."""

    def __init__(self, profile: Profile | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.profile = profile or Profile()
        self.setWindowTitle("Profil bearbeiten" if profile else "Neues Profil anlegen")
        self.resize(760, 780)
        self._build_ui()
        self._load_profile()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        intro = QLabel(
            "Stammdaten bleiben lokal. Zusatzfelder können später einzelnen "
            "Formularfeldern zugeordnet werden."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        participant = QGroupBox("Kind / teilnehmende Person")
        participant_form = QFormLayout(participant)
        self.display_name = QLineEdit()
        self.participant_first_name = QLineEdit()
        self.participant_last_name = QLineEdit()
        self.birth_date = QDateEdit()
        self.birth_date.setCalendarPopup(True)
        self.birth_date.setDisplayFormat("dd.MM.yyyy")
        self.birth_date.setMinimumDate(QDate(1900, 1, 1))
        self.birth_date.setMaximumDate(QDate.currentDate())
        self.birth_date_enabled = QCheckBox("Geburtsdatum verwenden")
        self.birth_date_enabled.toggled.connect(self.birth_date.setEnabled)
        participant_form.addRow("Profilname", self.display_name)
        participant_form.addRow("Vorname *", self.participant_first_name)
        participant_form.addRow("Nachname *", self.participant_last_name)
        birth_row = QHBoxLayout()
        birth_row.addWidget(self.birth_date)
        birth_row.addWidget(self.birth_date_enabled)
        participant_form.addRow("Geburtsdatum", birth_row)
        layout.addWidget(participant)

        address = QGroupBox("Anschrift und Kontakt")
        address_grid = QGridLayout(address)
        self.street = QLineEdit()
        self.postal_code = QLineEdit()
        self.postal_code.setMaxLength(10)
        self.city = QLineEdit()
        self.phone = QLineEdit()
        self.email = QLineEdit()
        address_grid.addWidget(QLabel("Straße"), 0, 0)
        address_grid.addWidget(self.street, 0, 1, 1, 3)
        address_grid.addWidget(QLabel("PLZ"), 1, 0)
        address_grid.addWidget(self.postal_code, 1, 1)
        address_grid.addWidget(QLabel("Ort"), 1, 2)
        address_grid.addWidget(self.city, 1, 3)
        address_grid.addWidget(QLabel("Telefon"), 2, 0)
        address_grid.addWidget(self.phone, 2, 1)
        address_grid.addWidget(QLabel("E-Mail"), 2, 2)
        address_grid.addWidget(self.email, 2, 3)
        address_grid.addWidget(
            QLabel("Ort wird zugleich als Vorschlag für den Unterschriftsort verwendet."),
            3,
            0,
            1,
            4,
        )
        layout.addWidget(address)

        guardians = QGroupBox("Erziehungsberechtigte Personen")
        guardians_layout = QVBoxLayout(guardians)
        self.copy_last_names = QCheckBox("Nachname des Kindes für leere Nachnamen übernehmen")
        self.copy_last_names.setChecked(True)
        guardians_layout.addWidget(self.copy_last_names)
        grid = QGridLayout()
        headers = ["", "Vorname", "Nachname", "E-Mail", "Telefon"]
        for column, text in enumerate(headers):
            grid.addWidget(QLabel(text), 0, column)
        self.guardian_fields: list[tuple[QLineEdit, QLineEdit, QLineEdit, QLineEdit]] = []
        for row in range(1, 3):
            first_name = QLineEdit()
            last_name = QLineEdit()
            email = QLineEdit()
            phone = QLineEdit()
            self.guardian_fields.append((first_name, last_name, email, phone))
            grid.addWidget(QLabel(f"Person {row}"), row, 0)
            grid.addWidget(first_name, row, 1)
            grid.addWidget(last_name, row, 2)
            grid.addWidget(email, row, 3)
            grid.addWidget(phone, row, 4)
        guardians_layout.addLayout(grid)
        layout.addWidget(guardians)

        custom = QGroupBox("Benutzerdefinierte Profilfelder")
        custom_layout = QVBoxLayout(custom)
        self.custom_table = QTableWidget(0, 4)
        self.custom_table.setHorizontalHeaderLabels(
            ["Bezeichnung", "Technischer Name", "Wert", "Schutz"]
        )
        header = self.custom_table.horizontalHeader()
        assert header is not None
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        custom_layout.addWidget(self.custom_table)
        custom_actions = QHBoxLayout()
        add_custom = QPushButton("Feld hinzufügen")
        add_custom.clicked.connect(self._add_custom_row)
        remove_custom = QPushButton("Ausgewähltes Feld entfernen")
        remove_custom.clicked.connect(self._remove_custom_row)
        custom_actions.addWidget(add_custom)
        custom_actions.addWidget(remove_custom)
        custom_actions.addStretch()
        custom_layout.addLayout(custom_actions)
        layout.addWidget(custom)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        save_button = buttons.button(QDialogButtonBox.StandardButton.Save)
        assert save_button is not None
        save_button.setText("Profil speichern")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_profile(self) -> None:
        profile = self.profile
        self.display_name.setText(profile.display_name)
        self.participant_first_name.setText(profile.participant_first_name)
        self.participant_last_name.setText(profile.participant_last_name)
        has_birth_date = profile.birth_date is not None
        self.birth_date_enabled.setChecked(has_birth_date)
        self.birth_date.setEnabled(has_birth_date)
        birth = profile.birth_date or date.today()
        self.birth_date.setDate(QDate(birth.year, birth.month, birth.day))
        self.street.setText(profile.street)
        self.postal_code.setText(profile.postal_code)
        self.city.setText(profile.city)
        self.phone.setText(profile.phone)
        self.email.setText(profile.email)
        for widgets, guardian in zip(
            self.guardian_fields,
            (profile.guardian_1, profile.guardian_2),
            strict=True,
        ):
            for widget, value in zip(
                widgets,
                (guardian.first_name, guardian.last_name, guardian.email, guardian.phone),
                strict=True,
            ):
                widget.setText(value)
        for custom_field in profile.custom_fields:
            self._add_custom_row(custom_field)

    def _add_custom_row(self, custom_field: CustomField | None = None) -> None:
        row = self.custom_table.rowCount()
        self.custom_table.insertRow(row)
        label = QTableWidgetItem(custom_field.label if custom_field else "")
        key = QTableWidgetItem(custom_field.key if custom_field else "")
        value = QTableWidgetItem(custom_field.value if custom_field else "")
        sensitivity = QComboBox()
        sensitivity.addItem("Normal", FieldSensitivity.NORMAL.value)
        sensitivity.addItem("Sensibel", FieldSensitivity.SENSITIVE.value)
        sensitivity.addItem("Besonders sensibel", FieldSensitivity.HIGHLY_SENSITIVE.value)
        if custom_field:
            sensitivity.setCurrentIndex(
                max(0, sensitivity.findData(custom_field.sensitivity.value))
            )
        self.custom_table.setItem(row, 0, label)
        self.custom_table.setItem(row, 1, key)
        self.custom_table.setItem(row, 2, value)
        self.custom_table.setCellWidget(row, 3, sensitivity)

    def _remove_custom_row(self) -> None:
        row = self.custom_table.currentRow()
        if row >= 0:
            self.custom_table.removeRow(row)

    def _validate_and_accept(self) -> None:
        candidate = self.result_profile()
        errors = candidate.validate()
        if errors:
            QMessageBox.warning(
                self,
                "Profil noch unvollständig",
                "\n".join(f"• {message}" for message in errors.values()),
            )
            return
        self.profile = candidate
        self.accept()

    def result_profile(self) -> Profile:
        """Build the profile represented by the current controls."""
        participant_last_name = self.participant_last_name.text().strip()
        guardians: list[Guardian] = []
        for first_name, last_name, email, phone in self.guardian_fields:
            resolved_last_name = last_name.text().strip()
            if (
                self.copy_last_names.isChecked()
                and first_name.text().strip()
                and not resolved_last_name
            ):
                resolved_last_name = participant_last_name
            guardians.append(
                Guardian(
                    first_name=first_name.text().strip(),
                    last_name=resolved_last_name,
                    email=email.text().strip(),
                    phone=phone.text().strip(),
                )
            )
        custom_fields: list[CustomField] = []
        for row in range(self.custom_table.rowCount()):
            label_item = self.custom_table.item(row, 0)
            key_item = self.custom_table.item(row, 1)
            value_item = self.custom_table.item(row, 2)
            label = label_item.text().strip() if label_item else ""
            key = key_item.text().strip().casefold() if key_item else ""
            if label and not key:
                key = _KEY_SANITIZER.sub("_", label.casefold()).strip("_")
            if not label and not key:
                continue
            sensitivity = self.custom_table.cellWidget(row, 3)
            sensitivity_value = (
                sensitivity.currentData()
                if isinstance(sensitivity, QComboBox)
                else FieldSensitivity.NORMAL.value
            )
            custom_fields.append(
                CustomField(
                    key=key,
                    label=label or key,
                    value=value_item.text().strip() if value_item else "",
                    sensitivity=FieldSensitivity(str(sensitivity_value)),
                )
            )
        selected_date = self.birth_date.date()
        birth_date = (
            date(selected_date.year(), selected_date.month(), selected_date.day())
            if self.birth_date_enabled.isChecked()
            else None
        )
        return Profile(
            id=self.profile.id,
            display_name=self.display_name.text().strip(),
            participant_first_name=self.participant_first_name.text().strip(),
            participant_last_name=participant_last_name,
            birth_date=birth_date,
            street=self.street.text().strip(),
            postal_code=self.postal_code.text().strip(),
            city=self.city.text().strip(),
            phone=self.phone.text().strip(),
            email=self.email.text().strip(),
            guardian_1=guardians[0],
            guardian_2=guardians[1],
            custom_fields=custom_fields,
        )
