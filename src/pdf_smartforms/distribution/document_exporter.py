"""Create a user-selected PDF work copy."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pymupdf

from pdf_smartforms.domain.distribution import PlacedSignature, PlacedText


def export_work_copy(
    source_pdf: Path,
    target_pdf: Path,
    signatures: list[PlacedSignature],
    texts: list[PlacedText] | None = None,
) -> Path:
    """Copy the source and visibly embed confirmed profile values and signatures."""
    document: Any = pymupdf.open(source_pdf)  # type: ignore[no-untyped-call]
    try:
        for placement in texts or []:
            if not 0 <= placement.page < document.page_count:
                raise ValueError("Textfeld verweist auf eine ungültige PDF-Seite.")
            page = document.load_page(placement.page)
            available_width = max(10, placement.x1 - placement.x0 - 4)
            font_size = min(
                placement.font_size,
                available_width
                / max(
                    1,
                    pymupdf.get_text_length(
                        placement.value,
                        fontname=_pdf_font_name(placement.font_family),
                        fontsize=1,
                    ),
                ),
            )
            baseline = placement.y0 + (placement.y1 - placement.y0 + font_size * 0.7) / 2
            page.insert_text(
                (placement.x0 + 2, baseline),
                placement.value,
                fontsize=font_size,
                fontname=_pdf_font_name(placement.font_family),
                color=(0, 0, 0),
            )
        for signature in signatures:
            if not 0 <= signature.page < document.page_count:
                raise ValueError("Unterschrift verweist auf eine ungültige PDF-Seite.")
            image_path = Path(signature.image_path)
            if not image_path.exists():
                raise ValueError("Eine verwendete Unterschriftsdatei fehlt.")
            page = document.load_page(signature.page)
            rectangle = pymupdf.Rect(  # type: ignore[no-untyped-call]
                signature.x0,
                signature.y0,
                signature.x1,
                signature.y1,
            )
            page.insert_image(rectangle, filename=str(image_path), keep_proportion=True)
        target_pdf.parent.mkdir(parents=True, exist_ok=True)
        document.save(target_pdf, garbage=4, deflate=True)
    finally:
        document.close()
    return target_pdf


def _pdf_font_name(family: str) -> str:
    normalized = family.casefold()
    if "courier" in normalized:
        return "cour"
    if "times" in normalized:
        return "tiro"
    return "helv"
