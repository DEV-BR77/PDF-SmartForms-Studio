"""Template and PDF coordinate domain model."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class TemplateStatus(StrEnum):
    """Trust status of one template."""

    VERIFIED = "verified"
    COMMUNITY = "community"
    EXPERIMENTAL = "experimental"
    LOCAL = "local"


class TemplateFieldType(StrEnum):
    """Supported field types independent of a PDF library."""

    TEXT = "text"
    MULTILINE = "multiline"
    DATE = "date"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    CHOICE = "choice"
    SIGNATURE_IMAGE = "signature_image"
    DIGITAL_SIGNATURE = "digital_signature"


@dataclass(frozen=True, slots=True)
class Rect:
    """Rectangle in PDF points using top-left preview coordinates."""

    x0: float
    y0: float
    x1: float
    y1: float

    def __post_init__(self) -> None:
        if self.x1 <= self.x0 or self.y1 <= self.y0:
            raise ValueError("Rechteck benötigt positive Breite und Höhe.")

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    def rotated(self, page_width: float, page_height: float, degrees: int) -> Rect:
        """Rotate a rectangle clockwise around the page for preview mapping."""
        normalized = degrees % 360
        if normalized == 0:
            return self
        if normalized == 90:
            return Rect(page_height - self.y1, self.x0, page_height - self.y0, self.x1)
        if normalized == 180:
            return Rect(
                page_width - self.x1,
                page_height - self.y1,
                page_width - self.x0,
                page_height - self.y0,
            )
        if normalized == 270:
            return Rect(self.y0, page_width - self.x1, self.y1, page_width - self.x0)
        raise ValueError("Nur 0, 90, 180 oder 270 Grad werden unterstützt.")


@dataclass(slots=True)
class TemplateField:
    """One field placement and its profile/runtime source."""

    id: str
    label: str
    type: TemplateFieldType
    page: int
    rect: Rect
    source: str = ""
    required: bool = False


@dataclass(slots=True)
class Template:
    """Versioned description of a reusable PDF form."""

    id: str
    name: str
    version: str
    language: str
    status: TemplateStatus
    minimum_app_version: str
    source_pdf: str
    source_pdf_license: str = ""
    document_fingerprint: str = ""
    fields: list[TemplateField] = field(default_factory=list)

    def validate(self) -> dict[str, str]:
        """Return errors suitable for UI display."""
        errors: dict[str, str] = {}
        if not self.id or any(
            character not in "abcdefghijklmnopqrstuvwxyz0123456789._-" for character in self.id
        ):
            errors["id"] = "Template-ID enthält unzulässige Zeichen."
        if not self.name.strip():
            errors["name"] = "Template-Name fehlt."
        if not self.version.strip():
            errors["version"] = "Template-Version fehlt."
        if not self.source_pdf.lower().endswith(".pdf"):
            errors["source_pdf"] = "Ein PDF als Quelldokument fehlt."
        field_ids = [item.id for item in self.fields]
        if len(field_ids) != len(set(field_ids)):
            errors["fields"] = "Feld-IDs müssen eindeutig sein."
        if any(item.page < 0 for item in self.fields):
            errors["page"] = "Seitennummern dürfen nicht negativ sein."
        return errors

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        for index, item in enumerate(self.fields):
            payload["fields"][index]["type"] = item.type.value
            payload["fields"][index]["rect"] = [
                item.rect.x0,
                item.rect.y0,
                item.rect.x1,
                item.rect.y1,
            ]
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Template:
        fields = [
            TemplateField(
                id=str(item["id"]),
                label=str(item["label"]),
                type=TemplateFieldType(item["type"]),
                page=int(item["page"]),
                rect=Rect(*(float(value) for value in item["rect"])),
                source=str(item.get("source", "")),
                required=bool(item.get("required", False)),
            )
            for item in payload.get("fields", [])
        ]
        return cls(
            id=str(payload["id"]),
            name=str(payload["name"]),
            version=str(payload["version"]),
            language=str(payload["language"]),
            status=TemplateStatus(payload["status"]),
            minimum_app_version=str(payload["minimum_app_version"]),
            source_pdf=str(payload["source_pdf"]),
            source_pdf_license=str(payload.get("source_pdf_license", "")),
            document_fingerprint=str(payload.get("document_fingerprint", "")),
            fields=fields,
        )
