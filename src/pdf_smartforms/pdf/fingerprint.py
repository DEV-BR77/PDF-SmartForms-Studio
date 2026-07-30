"""Stable document fingerprints for automatic local template recognition."""

# mypy: disable-error-code="no-untyped-call,attr-defined"

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pymupdf


def document_fingerprint(pdf_path: Path) -> str:
    """Hash stable PDF metadata, page geometry and normalized visible text."""
    try:
        document = pymupdf.open(pdf_path)
    except (OSError, RuntimeError) as error:
        raise ValueError("Der Dokumentfingerabdruck konnte nicht erstellt werden.") from error
    try:
        metadata = document.metadata or {}
        stable_metadata = {
            key: _normalize(str(metadata.get(key, "")))
            for key in ("title", "author", "subject", "keywords")
            if metadata.get(key)
        }
        pages = [
            {
                "width": round(float(page.rect.width), 1),
                "height": round(float(page.rect.height), 1),
                "rotation": int(page.rotation),
                "text": _stable_page_text(page),
            }
            for page in document
        ]
    finally:
        document.close()
    payload = json.dumps(
        {"metadata": stable_metadata, "pages": pages},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _stable_page_text(page: pymupdf.Page) -> str:
    """Ignore widget appearances and entered values while hashing page text."""
    widget_rects = [pymupdf.Rect(widget.rect) for widget in page.widgets() or ()]
    words: list[str] = []
    for word in page.get_text("words", sort=True):
        rect = pymupdf.Rect(*(float(value) for value in word[:4]))
        center = (rect.tl + rect.br) / 2
        if any(widget_rect.contains(center) for widget_rect in widget_rects):
            continue
        token = str(word[4]).strip()
        if token in {"☐", "□", "❏", "☒"} or (
            token and set(token) <= {"_", ".", "-"} and len(token) >= 5
        ):
            continue
        words.append(token)
    return _normalize(" ".join(words))
