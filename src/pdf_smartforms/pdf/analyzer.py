"""Read-only PDF form analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pymupdf

from pdf_smartforms.domain.detection import AnalysisResult, DetectedField, MatchStatus
from pdf_smartforms.domain.field_dictionary import FieldDictionary, normalize_label
from pdf_smartforms.domain.templates import Rect, TemplateFieldType

MAX_PDF_SIZE = 100 * 1024 * 1024
MAX_PAGES = 250


class PdfAnalysisError(ValueError):
    """Raised when a PDF cannot be inspected safely."""


def match_label(
    label: str, dictionary: FieldDictionary | None = None
) -> tuple[str | None, MatchStatus, float]:
    """Map a label to a known profile source without cloud services."""
    return (dictionary or FieldDictionary.with_seed_data()).match(label)


def analyze_pdf(path: Path, dictionary: FieldDictionary | None = None) -> AnalysisResult:
    """Inspect fields and text without executing actions or modifying the file."""
    if path.suffix.casefold() != ".pdf":
        raise PdfAnalysisError("Die ausgewählte Datei ist kein PDF.")
    if not path.exists() or path.stat().st_size > MAX_PDF_SIZE:
        raise PdfAnalysisError("PDF fehlt oder überschreitet das Größenlimit.")
    try:
        document = pymupdf.open(path)
    except (pymupdf.FileDataError, RuntimeError) as error:
        raise PdfAnalysisError(
            "PDF ist beschädigt oder kann nicht sicher gelesen werden."
        ) from error
    with document:
        if document.needs_pass:
            raise PdfAnalysisError("Passwortgeschützte PDFs werden nicht umgangen.")
        if document.page_count > MAX_PAGES:
            raise PdfAnalysisError("PDF überschreitet die unterstützte Seitenzahl.")
        active_dictionary = dictionary or FieldDictionary.with_seed_data()
        fields: list[DetectedField] = []
        for page_number, page in enumerate(document):
            widget_fields = _analyze_widgets(page, page_number, active_dictionary)
            fields.extend(widget_fields)
            if not widget_fields:
                fields.extend(_analyze_flat_page(page, page_number, active_dictionary))
        title = str(document.metadata.get("title") or "").strip() or path.stem
        warnings = (
            ("Keine Formularfelder erkannt. Im Designer können Felder manuell angelegt werden.",)
            if not fields
            else ()
        )
        return AnalysisResult(title, document.page_count, tuple(fields), warnings)


def render_page(path: Path, page_number: int, scale: float = 1.5) -> tuple[bytes, int, int]:
    with pymupdf.open(path) as document:
        page = document.load_page(page_number)
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
        return pixmap.samples, pixmap.width, pixmap.height


def _analyze_widgets(
    page: Any, page_number: int, dictionary: FieldDictionary
) -> list[DetectedField]:
    fields: list[DetectedField] = []
    widgets = page.widgets()
    if widgets is None:
        return fields
    for index, widget in enumerate(widgets):
        label = str(widget.field_label or widget.field_name or f"Feld {index + 1}")
        match_value = str(widget.field_label or widget.field_name or "").replace("_", " ")
        source, status, confidence = match_label(match_value, dictionary)
        rect = widget.rect
        fields.append(
            DetectedField(
                f"acroform-{page_number}-{index}",
                label,
                _widget_type(widget.field_type_string or ""),
                page_number,
                Rect(rect.x0, rect.y0, rect.x1, rect.y1),
                source,
                status,
                confidence,
                "AcroForm",
            )
        )
    return fields


def _analyze_flat_page(
    page: Any, page_number: int, dictionary: FieldDictionary
) -> list[DetectedField]:
    fields: list[DetectedField] = []
    seen: set[tuple[int, int]] = set()
    aliases = sorted(
        {alias for values in dictionary.entries.values() for alias in values},
        key=len,
        reverse=True,
    )
    for alias in aliases:
        for occurrence in page.search_for(alias):
            position = (round(occurrence.y0), round(occurrence.x0))
            if position in seen:
                continue
            seen.add(position)
            source, status, confidence = match_label(alias, dictionary)
            x0 = min(occurrence.x1 + 8, page.rect.width - 80)
            x1 = max(x0 + 72, page.rect.width - 36)
            y0 = max(0, occurrence.y0 - 3)
            y1 = min(page.rect.height, max(occurrence.y1 + 6, y0 + 18))
            fields.append(
                DetectedField(
                    f"text-{page_number}-{len(fields)}",
                    alias,
                    _guess_field_type(alias),
                    page_number,
                    Rect(x0, y0, x1, y1),
                    source,
                    status,
                    min(confidence, 0.9),
                    "Textanalyse",
                )
            )
    for word in page.get_text("words"):
        text = str(word[4]).strip()
        if not text.endswith(":") or len(text) < 3:
            continue
        label = text.rstrip(":")
        if any(normalize_label(label) == normalize_label(item.label) for item in fields):
            continue
        source, status, confidence = match_label(label, dictionary)
        x0 = min(float(word[2]) + 8, page.rect.width - 80)
        x1 = max(x0 + 72, page.rect.width - 36)
        fields.append(
            DetectedField(
                f"label-{page_number}-{len(fields)}",
                label,
                _guess_field_type(label),
                page_number,
                Rect(x0, float(word[1]) - 3, x1, float(word[3]) + 6),
                source,
                status,
                confidence,
                "Beschriftungsheuristik",
            )
        )
    return fields


def _widget_type(value: str) -> TemplateFieldType:
    normalized = value.casefold()
    if "check" in normalized:
        return TemplateFieldType.CHECKBOX
    if "radio" in normalized:
        return TemplateFieldType.RADIO
    if any(item in normalized for item in ("choice", "combo", "list")):
        return TemplateFieldType.CHOICE
    if "signature" in normalized:
        return TemplateFieldType.DIGITAL_SIGNATURE
    return TemplateFieldType.TEXT


def _guess_field_type(label: str) -> TemplateFieldType:
    normalized = normalize_label(label)
    if "datum" in normalized or "geboren" in normalized:
        return TemplateFieldType.DATE
    return TemplateFieldType.TEXT
