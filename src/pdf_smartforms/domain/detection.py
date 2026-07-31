"""PDF field detection results."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pdf_smartforms.domain.templates import Rect, TemplateFieldType


class MatchStatus(StrEnum):
    MAPPED = "mapped"
    UNCERTAIN = "uncertain"
    MISSING = "missing"


@dataclass(frozen=True, slots=True)
class DetectedField:
    id: str
    label: str
    type: TemplateFieldType
    page: int
    rect: Rect
    source: str | None
    status: MatchStatus
    confidence: float
    origin: str
    option_value: str = ""
    default_value: str = ""
    font_family: str = "Helvetica"
    font_size: float = 9.0

    @property
    def status_label(self) -> str:
        labels = {
            MatchStatus.MAPPED: "✓ Zugeordnet",
            MatchStatus.UNCERTAIN: "⚠ Prüfung erforderlich",
            MatchStatus.MISSING: "✕ Nicht zugeordnet",
        }
        return labels[self.status]


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    title: str
    page_count: int
    fields: tuple[DetectedField, ...]
    warnings: tuple[str, ...] = ()
