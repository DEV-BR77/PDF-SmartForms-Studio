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
        document: Any = pymupdf.open(path)  # type: ignore[no-untyped-call]
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
        for page_number in range(document.page_count):
            page: Any = document.load_page(page_number)
            widget_fields = _analyze_widgets(page, page_number, active_dictionary)
            fields.extend(widget_fields)
            if not widget_fields:
                fields.extend(_analyze_flat_page(page, page_number, active_dictionary))
        metadata: dict[str, Any] = document.metadata or {}
        title = str(metadata.get("title") or "").strip() or path.stem
        warnings = (
            ("Keine Formularfelder erkannt. Im Designer können Felder manuell angelegt werden.",)
            if not fields
            else ()
        )
        return AnalysisResult(title, document.page_count, tuple(fields), warnings)


def render_page(path: Path, page_number: int, scale: float = 1.5) -> tuple[bytes, int, int]:
    with pymupdf.open(path) as document:  # type: ignore[no-untyped-call]
        page = document.load_page(page_number)
        matrix = pymupdf.Matrix(scale, scale)  # type: ignore[no-untyped-call]
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
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
    aliases = sorted(
        {alias for values in dictionary.entries.values() for alias in values},
        key=len,
        reverse=True,
    )
    for text, bbox, font_size in _text_spans(page):
        if font_size < 8.0 or not _looks_like_label(text):
            continue
        label = text.strip().rstrip(":").strip()
        normalized = normalize_label(label)
        matching_alias = next(
            (
                alias
                for alias in aliases
                if normalized == normalize_label(alias)
                or normalized.startswith(f"{normalize_label(alias)} ")
            ),
            None,
        )
        if matching_alias is None and not text.rstrip().endswith(":"):
            continue
        source, status, confidence = match_label(matching_alias or label, dictionary)
        field_rect = _table_input_rect(page, bbox)
        if field_rect is None:
            if "@" in label or any(character.isdigit() for character in label):
                continue
            if matching_alias is None and font_size < 9.5:
                continue
            x0 = min(float(bbox[2]) + 8, page.rect.width - 80)
            x1 = max(x0 + 72, page.rect.width - 36)
            field_rect = Rect(
                x0,
                max(0, float(bbox[1]) - 3),
                x1,
                min(page.rect.height, float(bbox[3]) + 6),
            )
        fields.append(
            DetectedField(
                f"label-{page_number}-{len(fields)}",
                label,
                _guess_field_type(label),
                page_number,
                field_rect,
                source,
                status,
                min(confidence, 0.9),
                "Beschriftungsheuristik",
            )
        )
    fields.extend(_analyze_checkbox_glyphs(page, page_number, dictionary, len(fields)))
    fields.extend(_analyze_drawn_choice_boxes(page, page_number, dictionary, len(fields)))
    return fields


def _analyze_checkbox_glyphs(
    page: Any,
    page_number: int,
    dictionary: FieldDictionary,
    start_index: int,
) -> list[DetectedField]:
    """Detect visible empty checkbox glyphs, including common Ja/Nein choices."""
    words = list(page.get_text("words"))
    output: list[DetectedField] = []
    symbols = {"☐", "□", "❏", "☒"}
    for index, word in enumerate(words):
        if str(word[4]).strip() not in symbols:
            continue
        x0, y0, x1, y1 = (float(value) for value in word[:4])
        block, line = int(word[5]), int(word[6])
        same_line = [
            item
            for item in words
            if int(item[5]) == block
            and int(item[6]) == line
            and float(item[0]) >= x1 - 1
            and str(item[4]).strip() not in symbols
        ]
        option = str(min(same_line, key=lambda item: float(item[0]))[4]) if same_line else ""
        previous_lines: dict[tuple[int, int], list[Any]] = {}
        for candidate in words:
            candidate_bottom = float(candidate[3])
            candidate_text = str(candidate[4]).strip()
            if (
                candidate_bottom <= y0
                and y0 - candidate_bottom <= 85
                and candidate_text not in symbols
                and candidate_text.casefold() not in {"ja", "nein"}
            ):
                previous_lines.setdefault((int(candidate[5]), int(candidate[6])), []).append(
                    candidate
                )
        context = ""
        if previous_lines:
            nearest = max(
                previous_lines.values(),
                key=lambda items: max(float(item[3]) for item in items),
            )
            context = " ".join(
                str(item[4]) for item in sorted(nearest, key=lambda item: float(item[0]))
            ).strip()
        label = " – ".join(part for part in (context.rstrip(":"), option) if part)
        label = label or f"Auswahl {len(output) + 1}"
        source, status, confidence = match_label(context or label, dictionary)
        normalized_option = option.casefold().strip(".,:;!?")
        field_type = (
            TemplateFieldType.RADIO
            if normalized_option in {"ja", "nein"}
            else TemplateFieldType.CHECKBOX
        )
        output.append(
            DetectedField(
                f"choice-{page_number}-{start_index + index}",
                label,
                field_type,
                page_number,
                Rect(x0, y0, x1, y1),
                source,
                status,
                confidence,
                "Sichtbares Auswahlfeld",
            )
        )
    return output


def _analyze_drawn_choice_boxes(
    page: Any,
    page_number: int,
    dictionary: FieldDictionary,
    start_index: int,
) -> list[DetectedField]:
    """Detect small drawn boxes next to option labels."""
    words = list(page.get_text("words"))
    output: list[DetectedField] = []
    seen: set[tuple[float, float]] = set()
    for drawing in page.get_drawings():
        drawing_rect = drawing.get("rect")
        if drawing_rect is None or not (
            4 <= drawing_rect.width <= 20 and 4 <= drawing_rect.height <= 20
        ):
            continue
        marker = (round(float(drawing_rect.x0), 1), round(float(drawing_rect.y0), 1))
        if marker in seen:
            continue
        seen.add(marker)
        nearby = [
            word
            for word in words
            if float(word[0]) >= drawing_rect.x1 - 2
            and float(word[0]) <= drawing_rect.x1 + 80
            and abs(
                ((float(word[1]) + float(word[3])) / 2)
                - ((float(drawing_rect.y0) + float(drawing_rect.y1)) / 2)
            )
            <= 8
        ]
        if not nearby:
            continue
        option = str(min(nearby, key=lambda item: float(item[0]))[4]).strip()
        previous = [
            word
            for word in words
            if float(word[3]) <= drawing_rect.y0
            and drawing_rect.y0 - float(word[3]) <= 85
            and str(word[4]).casefold() not in {"ja", "nein"}
        ]
        context = ""
        if previous:
            nearest_line = max(previous, key=lambda item: float(item[3]))
            block, line = int(nearest_line[5]), int(nearest_line[6])
            context = " ".join(
                str(word[4])
                for word in sorted(
                    (word for word in words if int(word[5]) == block and int(word[6]) == line),
                    key=lambda item: float(item[0]),
                )
            ).strip()
        label = " – ".join(part for part in (context.rstrip(":"), option) if part)
        source, status, confidence = match_label(context or label, dictionary)
        output.append(
            DetectedField(
                f"drawn-choice-{page_number}-{start_index + len(output)}",
                label or f"Auswahl {len(output) + 1}",
                (
                    TemplateFieldType.RADIO
                    if option.casefold().strip(".,:;!?") in {"ja", "nein"}
                    else TemplateFieldType.CHECKBOX
                ),
                page_number,
                Rect(
                    float(drawing_rect.x0),
                    float(drawing_rect.y0),
                    float(drawing_rect.x1),
                    float(drawing_rect.y1),
                ),
                source,
                status,
                confidence,
                "Gezeichnetes Auswahlfeld",
            )
        )
    return output


def _table_input_rect(page: Any, bbox: tuple[float, float, float, float]) -> Rect | None:
    """Use nearby table borders instead of extending a label to the page edge."""
    center_y = (bbox[1] + bbox[3]) / 2
    vertical: list[tuple[float, float, float]] = []
    horizontal: list[tuple[float, float, float]] = []
    for drawing in page.get_drawings():
        rect = drawing.get("rect")
        if rect is None:
            continue
        if rect.width <= 1.5 and rect.height >= 8:
            vertical.append((float(rect.x0 + rect.x1) / 2, float(rect.y0), float(rect.y1)))
        if rect.height <= 1.5 and rect.width >= 30:
            horizontal.append((float(rect.y0 + rect.y1) / 2, float(rect.x0), float(rect.x1)))
        for item in drawing.get("items", []):
            if item[0] == "l":
                start, end = item[1], item[2]
                if abs(start.x - end.x) <= 1.5 and abs(start.y - end.y) >= 8:
                    vertical.append(
                        (float(start.x), float(min(start.y, end.y)), float(max(start.y, end.y)))
                    )
                if abs(start.y - end.y) <= 1.5 and abs(start.x - end.x) >= 30:
                    horizontal.append(
                        (float(start.y), float(min(start.x, end.x)), float(max(start.x, end.x)))
                    )
            if item[0] == "re":
                item_rect = item[1]
                if item_rect.width >= 30 and item_rect.height >= 8:
                    vertical.extend(
                        (
                            (float(item_rect.x0), float(item_rect.y0), float(item_rect.y1)),
                            (float(item_rect.x1), float(item_rect.y0), float(item_rect.y1)),
                        )
                    )
                    horizontal.extend(
                        (
                            (float(item_rect.y0), float(item_rect.x0), float(item_rect.x1)),
                            (float(item_rect.y1), float(item_rect.x0), float(item_rect.x1)),
                        )
                    )
    right_borders = sorted(
        {round(x, 1) for x, y0, y1 in vertical if y0 - 1 <= center_y <= y1 + 1 and x >= bbox[2] - 4}
    )
    if len(right_borders) < 2:
        return None
    x0, x1 = right_borders[0], right_borders[1]
    row_borders = sorted(
        {
            round(y, 1)
            for y, line_x0, line_x1 in horizontal
            if line_x0 <= x0 + 2 and line_x1 >= x1 - 2
        }
    )
    above = [y for y in row_borders if y <= center_y]
    below = [y for y in row_borders if y >= center_y]
    if not above or not below:
        return None
    y0, y1 = max(above), min(below)
    if y1 - y0 < 8 or x1 - x0 < 30:
        return None
    return Rect(x0 + 2, y0 + 2, x1 - 2, y1 - 2)


def _text_spans(page: Any) -> list[tuple[str, tuple[float, float, float, float], float]]:
    """Return visible text spans with geometry and font size."""
    output: list[tuple[str, tuple[float, float, float, float], float]] = []
    text_dictionary: dict[str, Any] = page.get_text("dict")
    for block in text_dictionary.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = str(span.get("text", "")).strip()
                bbox = span.get("bbox")
                if text and isinstance(bbox, (list, tuple)) and len(bbox) == 4:
                    coordinates = (
                        float(bbox[0]),
                        float(bbox[1]),
                        float(bbox[2]),
                        float(bbox[3]),
                    )
                    output.append(
                        (
                            text,
                            coordinates,
                            float(span.get("size", 0)),
                        )
                    )
    return output


def _looks_like_label(text: str) -> bool:
    """Reject paragraph fragments, tiny footer text and long legal prose."""
    normalized = normalize_label(text.rstrip(":"))
    non_fields = {"datenschutz", "geschäftsführer", "aufsichtsratsvorsitzende"}
    return (
        normalized not in non_fields and 2 <= len(normalized) <= 70 and len(normalized.split()) <= 9
    )


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
    if "unterschrift" in normalized:
        return TemplateFieldType.SIGNATURE_IMAGE
    return TemplateFieldType.TEXT
