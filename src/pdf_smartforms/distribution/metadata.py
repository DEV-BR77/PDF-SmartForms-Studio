"""Local title, recipient and subject suggestions."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pymupdf

from pdf_smartforms.domain.distribution import CommunicationSuggestion

_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)


def suggest_communication(path: Path) -> CommunicationSuggestion:
    """Read metadata and visible text locally; never sends anything."""
    with pymupdf.open(path) as document:  # type: ignore[no-untyped-call]
        metadata: dict[str, Any] = document.metadata or {}
        title = _visual_heading(document.load_page(0)) if document.page_count else ""
        first_page_text = document.load_page(0).get_text("text") if document.page_count else ""
        if not title:
            title = (
                str(metadata.get("title") or "").strip()
                or _first_heading(first_page_text)
                or path.stem
            )
        title = clean_document_title(title, path.stem)
        all_text = "\n".join(
            document.load_page(index).get_text("text") for index in range(document.page_count)
        )
    recipients = tuple(sorted({match.casefold() for match in _EMAIL.findall(all_text)}))
    return CommunicationSuggestion(
        title=title,
        subject=f"Ausgefülltes Formular: {title}",
        recipients=recipients,
    )


def suggest_publication_date(path: Path) -> str:
    """Suggest, but never assert, a publication date from PDF metadata."""
    with pymupdf.open(path) as document:  # type: ignore[no-untyped-call]
        metadata: dict[str, Any] = document.metadata or {}
    value = str(metadata.get("creationDate") or "")
    match = re.match(r"D:(\d{4})(\d{2})(\d{2})", value)
    return "-".join(match.groups()) if match else ""


def _first_heading(text: str) -> str:
    for line in text.splitlines():
        candidate = " ".join(line.split()).strip()
        if 4 <= len(candidate) <= 120 and not _EMAIL.fullmatch(candidate):
            return candidate
    return ""


def _visual_heading(page: Any) -> str:
    """Prefer the prominent visible form heading over internal PDF metadata."""
    text_dictionary: dict[str, Any] = page.get_text("dict")
    candidates: list[tuple[float, str]] = []
    for block in text_dictionary.get("blocks", []):
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            text = " ".join(str(span.get("text", "")).strip() for span in spans).strip()
            size = max((float(span.get("size", 0)) for span in spans), default=0)
            if size >= 13 and 5 <= len(text) <= 120:
                candidates.append((size, text))
    return max(candidates, default=(0, ""), key=lambda item: (item[0], len(item[1])))[1]


def clean_document_title(value: str, fallback: str) -> str:
    """Keep titles useful in windows, subjects and suggested filenames."""
    compact = " ".join(value.split()).strip()
    for separator in (" • ", " | ", " · ", " – "):
        compact = compact.split(separator, 1)[0].strip()
    return (compact or fallback).strip()[:80]
