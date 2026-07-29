"""Create a user-selected PDF work copy."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pymupdf

from pdf_smartforms.domain.distribution import PlacedSignature


def export_work_copy(
    source_pdf: Path,
    target_pdf: Path,
    signatures: list[PlacedSignature],
) -> Path:
    """Copy the source and visibly embed explicitly placed signature images."""
    document: Any = pymupdf.open(source_pdf)  # type: ignore[no-untyped-call]
    try:
        for placement in signatures:
            if not 0 <= placement.page < document.page_count:
                raise ValueError("Unterschrift verweist auf eine ungültige PDF-Seite.")
            image_path = Path(placement.image_path)
            if not image_path.exists():
                raise ValueError("Eine verwendete Unterschriftsdatei fehlt.")
            page = document.load_page(placement.page)
            rectangle = pymupdf.Rect(  # type: ignore[no-untyped-call]
                placement.x0,
                placement.y0,
                placement.x1,
                placement.y1,
            )
            page.insert_image(rectangle, filename=str(image_path), keep_proportion=True)
        target_pdf.parent.mkdir(parents=True, exist_ok=True)
        document.save(target_pdf, garbage=4, deflate=True)
    finally:
        document.close()
    return target_pdf
