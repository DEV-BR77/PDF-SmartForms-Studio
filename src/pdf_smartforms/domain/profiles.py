"""Profile domain model."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any
from uuid import uuid4


class FieldSensitivity(StrEnum):
    """Protection level for profile values."""

    NORMAL = "normal"
    SENSITIVE = "sensitive"
    HIGHLY_SENSITIVE = "highly_sensitive"


@dataclass(slots=True)
class Guardian:
    """One parent or legal guardian."""

    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""


@dataclass(slots=True)
class CustomField:
    """A user-defined value not covered by the stable core schema."""

    key: str
    label: str
    value: str = ""
    sensitivity: FieldSensitivity = FieldSensitivity.NORMAL
    include_in_exports: bool = True


@dataclass(slots=True)
class Profile:
    """Reusable participant and household data."""

    id: str = field(default_factory=lambda: str(uuid4()))
    display_name: str = ""
    participant_first_name: str = ""
    participant_last_name: str = ""
    birth_date: date | None = None
    street: str = ""
    postal_code: str = ""
    city: str = ""
    phone: str = ""
    email: str = ""
    guardian_1: Guardian = field(default_factory=Guardian)
    guardian_2: Guardian = field(default_factory=Guardian)
    custom_fields: list[CustomField] = field(default_factory=list)

    def effective_display_name(self) -> str:
        """Return the explicit label or a stable human-readable fallback."""
        explicit = self.display_name.strip()
        if explicit:
            return explicit
        full_name = f"{self.participant_first_name} {self.participant_last_name}".strip()
        return full_name or "Unbenanntes Profil"

    def validate(self) -> dict[str, str]:
        """Return field-specific validation messages."""
        errors: dict[str, str] = {}
        if not self.participant_first_name.strip():
            errors["participant_first_name"] = "Vorname des Kindes fehlt."
        if not self.participant_last_name.strip():
            errors["participant_last_name"] = "Nachname des Kindes fehlt."
        if self.email and "@" not in self.email:
            errors["email"] = "Die E-Mail-Adresse ist ungültig."
        for prefix, guardian in (
            ("guardian_1", self.guardian_1),
            ("guardian_2", self.guardian_2),
        ):
            if guardian.email and "@" not in guardian.email:
                errors[f"{prefix}.email"] = "Die E-Mail-Adresse ist ungültig."
        duplicate_keys = {
            custom.key
            for custom in self.custom_fields
            if sum(item.key == custom.key for item in self.custom_fields) > 1
        }
        if duplicate_keys:
            errors["custom_fields"] = "Technische Namen der Zusatzfelder müssen eindeutig sein."
        return errors

    def to_dict(self) -> dict[str, Any]:
        """Serialize to an open JSON-compatible representation."""
        payload = asdict(self)
        payload["birth_date"] = self.birth_date.isoformat() if self.birth_date else None
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Profile:
        """Read a profile while tolerating missing fields from older schemas."""
        birth_value = payload.get("birth_date")
        custom_fields = [
            CustomField(
                key=str(item["key"]),
                label=str(item["label"]),
                value=str(item.get("value", "")),
                sensitivity=FieldSensitivity(item.get("sensitivity", "normal")),
                include_in_exports=bool(item.get("include_in_exports", True)),
            )
            for item in payload.get("custom_fields", [])
        ]
        return cls(
            id=str(payload.get("id") or uuid4()),
            display_name=str(payload.get("display_name", "")),
            participant_first_name=str(payload.get("participant_first_name", "")),
            participant_last_name=str(payload.get("participant_last_name", "")),
            birth_date=date.fromisoformat(str(birth_value)) if birth_value else None,
            street=str(payload.get("street", "")),
            postal_code=str(payload.get("postal_code", "")),
            city=str(payload.get("city", "")),
            phone=str(payload.get("phone", "")),
            email=str(payload.get("email", "")),
            guardian_1=Guardian(**payload.get("guardian_1", {})),
            guardian_2=Guardian(**payload.get("guardian_2", {})),
            custom_fields=custom_fields,
        )
