"""Mandatory review shown before document output actions."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from pdf_smartforms.domain.safety import SafetyReview


class SafetyReviewDialog(QDialog):
    """Require an explicit confirmation of visible output details."""

    def __init__(self, review: SafetyReview, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.review = review
        self.setWindowTitle(f"Sicherheitsvorschau · {review.action}")
        self.setMinimumWidth(560)
        layout = QVBoxLayout(self)
        heading = QLabel("Bitte vor dem Fortfahren prüfen")
        heading.setObjectName("title")
        layout.addWidget(heading)
        explanation = QLabel(
            "Die Anwendung führt die Aktion erst aus, nachdem du die Zusammenfassung "
            "geprüft und ausdrücklich bestätigt hast."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)

        facts = QFormLayout()
        facts.addRow("Aktion", QLabel(review.action))
        facts.addRow("Dokument", QLabel(review.document_name))
        facts.addRow("Zugeordnete Felder", QLabel(str(review.mapped_fields)))
        unresolved = QLabel(str(review.unresolved_fields))
        if review.unresolved_fields:
            unresolved.setText(f"⚠ {review.unresolved_fields} – bitte im Formular prüfen")
        facts.addRow("Nicht zugeordnet", unresolved)
        facts.addRow("Bildunterschriften", QLabel(str(review.signatures)))
        if review.recipients or review.action == "E-Mail-Entwurf":
            facts.addRow("Empfänger", QLabel(", ".join(review.recipients) or "⚠ nicht angegeben"))
        if review.subject:
            subject = QLabel(review.subject)
            subject.setWordWrap(True)
            facts.addRow("Betreff", subject)
        if review.attachments:
            facts.addRow("Anhänge", QLabel(", ".join(review.attachments)))
        layout.addLayout(facts)

        self.confirmation = QCheckBox(
            "Ich habe Dokument, Felder, Unterschriften und gegebenenfalls Empfänger geprüft."
        )
        self.confirmation.setAccessibleName("Sicherheitsprüfung bestätigen")
        layout.addWidget(self.confirmation)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if self.ok_button is None:
            raise RuntimeError("Bestätigungsschaltfläche konnte nicht erstellt werden.")
        self.ok_button.setText(review.action)
        self.ok_button.setEnabled(False)
        self.confirmation.toggled.connect(self.ok_button.setEnabled)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


def confirm_safety_review(review: SafetyReview, parent: QWidget | None = None) -> bool:
    """Return true only after an explicit, informed confirmation."""
    return SafetyReviewDialog(review, parent).exec() == QDialog.DialogCode.Accepted
