"""Models used by the final safety review."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SafetyReview:
    """Human-readable facts that must be confirmed before an output action."""

    action: str
    document_name: str
    mapped_fields: int
    unresolved_fields: int
    signatures: int
    recipients: tuple[str, ...] = ()
    subject: str = ""
    attachments: tuple[str, ...] = ()

    @property
    def has_warnings(self) -> bool:
        return self.unresolved_fields > 0 or (
            self.action == "E-Mail-Entwurf" and not self.recipients
        )
