"""Build self-contained template packages."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from pdf_smartforms.domain.templates import Template
from pdf_smartforms.templates.package_importer import inspect_package


def build_template_package(
    template: Template,
    source_pdf: Path,
    target: Path,
) -> Path:
    """Create and self-validate a portable `.psfstemplate` archive."""
    errors = template.validate()
    if errors:
        raise ValueError("; ".join(errors.values()))
    if not source_pdf.exists() or source_pdf.suffix.casefold() != ".pdf":
        raise ValueError("Quell-PDF fehlt.")
    if template.source_pdf != source_pdf.name:
        raise ValueError("Template und PDF-Dateiname stimmen nicht überein.")
    manifest = json.dumps(
        template.to_dict(),
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")
    pdf_bytes = source_pdf.read_bytes()
    checksums = json.dumps(
        {
            "template.json": hashlib.sha256(manifest).hexdigest(),
            source_pdf.name: hashlib.sha256(pdf_bytes).hexdigest(),
        },
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("template.json", manifest)
        archive.writestr(source_pdf.name, pdf_bytes)
        archive.writestr("checksums.json", checksums)
    inspect_package(target)
    return target
