"""User-confirmed metadata for searchable template catalogs."""

from __future__ import annotations

from datetime import date, datetime

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from pdf_smartforms.domain.templates import TemplateMetadata

_CATEGORIES = [
    ("Bitte auswählen", ""),
    ("Bildung", "education"),
    ("Finanzen", "finance"),
    ("Behörde", "government"),
    ("Gesundheit", "health"),
    ("Verein", "club"),
    ("Unternehmen", "company"),
    ("Sonstiges", "other"),
]


class TemplateMetadataDialog(QDialog):
    """Collect catalog metadata while clearly marking automatic suggestions."""

    def __init__(
        self,
        institution_suggestion: str = "",
        city_suggestion: str = "",
        publication_suggestion: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Angaben zur Vorlage")
        self.resize(560, 650)
        layout = QVBoxLayout(self)
        explanation = QLabel(
            "Diese Angaben helfen bei Suche, Aktualisierung und automatischer "
            "Dokumenterkennung. Vorschläge bitte vor dem Speichern prüfen."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        form = QFormLayout()
        self.institution = QLineEdit(institution_suggestion)
        self.category = QComboBox()
        for label, value in _CATEGORIES:
            self.category.addItem(label, value)
        self.institution_type = QLineEdit()
        self.institution_subtype = QLineEdit()
        self.country = QLineEdit("DE")
        self.state = QLineEdit()
        self.city = QLineEdit(city_suggestion)
        self.scope = QLineEdit()
        self.document_type = QLineEdit()
        self.target_group = QLineEdit()
        self.published = QLineEdit(publication_suggestion)
        self.valid_from = QLineEdit()
        self.valid_until = QLineEdit()
        self.keywords = QLineEdit()
        for widget in (self.published, self.valid_from, self.valid_until):
            widget.setPlaceholderText("JJJJ-MM-TT")
        form.addRow("Institution", self.institution)
        form.addRow("Kategorie", self.category)
        form.addRow("Art", self.institution_type)
        form.addRow("Unterart", self.institution_subtype)
        form.addRow("Land", self.country)
        form.addRow("Bundesland", self.state)
        form.addRow("Ort", self.city)
        form.addRow("Gültigkeitsbereich", self.scope)
        form.addRow("Dokumentart", self.document_type)
        form.addRow("Zielgruppe", self.target_group)
        form.addRow("Veröffentlicht am", self.published)
        form.addRow("Gültig ab", self.valid_from)
        form.addRow("Gültig bis", self.valid_until)
        form.addRow("Schlagwörter", self.keywords)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        save = buttons.button(QDialogButtonBox.StandardButton.Save)
        if save is not None:
            save.setText("Angaben übernehmen")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_accept(self) -> None:
        for label, widget in (
            ("Veröffentlichungsdatum", self.published),
            ("Gültig ab", self.valid_from),
            ("Gültig bis", self.valid_until),
        ):
            value = widget.text().strip()
            if value:
                try:
                    date.fromisoformat(value)
                except ValueError:
                    QMessageBox.warning(
                        self,
                        "Datum prüfen",
                        f"{label} muss im Format JJJJ-MM-TT angegeben werden.",
                    )
                    widget.setFocus()
                    return
        self.accept()

    def metadata(self) -> TemplateMetadata:
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        return TemplateMetadata(
            institution_name=self.institution.text().strip(),
            institution_category=str(self.category.currentData() or ""),
            institution_type=self.institution_type.text().strip(),
            institution_subtype=self.institution_subtype.text().strip(),
            country=self.country.text().strip().upper(),
            state=self.state.text().strip(),
            city=self.city.text().strip(),
            geographic_scope=self.scope.text().strip(),
            document_type=self.document_type.text().strip(),
            target_group=self.target_group.text().strip(),
            document_published_at=self.published.text().strip(),
            valid_from=self.valid_from.text().strip(),
            valid_until=self.valid_until.text().strip(),
            template_created_at=now,
            template_updated_at=now,
            keywords=tuple(
                item.strip() for item in self.keywords.text().split(",") if item.strip()
            ),
        )
