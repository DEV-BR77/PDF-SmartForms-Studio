"""Distribution and document-output models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class DistributionList:
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    recipients: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "recipients": self.recipients}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DistributionList:
        return cls(
            id=str(payload["id"]),
            name=str(payload["name"]),
            recipients=[str(item) for item in payload.get("recipients", [])],
        )


@dataclass(frozen=True, slots=True)
class CommunicationSuggestion:
    title: str
    subject: str
    recipients: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PlacedSignature:
    image_path: str
    page: int
    x0: float
    y0: float
    x1: float
    y1: float
