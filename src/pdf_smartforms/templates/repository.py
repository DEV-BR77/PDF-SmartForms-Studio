"""Local template repository."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from pdf_smartforms.domain.templates import Template
from pdf_smartforms.templates.package_importer import inspect_package, read_validated_files


class TemplateRepository:
    """Install and list immutable template versions."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[Template]:
        templates: list[Template] = []
        for manifest in self.directory.glob("*/*/template.json"):
            try:
                payload = json.loads(manifest.read_text(encoding="utf-8"))
                templates.append(Template.from_dict(payload))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue
        return sorted(templates, key=lambda item: (item.name.casefold(), item.version))

    def install_package(self, package_path: Path) -> Template:
        """Validate and install a package without overwriting existing versions."""
        inspected = inspect_package(package_path)
        target = self._version_directory(inspected.template)
        if target.exists():
            raise FileExistsError(
                f"{inspected.template.name} {inspected.template.version} ist bereits installiert."
            )
        staging = target.with_name(f".{target.name}.installing")
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)
        try:
            for name, content in read_validated_files(package_path).items():
                (staging / name).write_bytes(content)
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staging, target)
        except Exception:
            if staging.exists():
                shutil.rmtree(staging)
            raise
        return inspected.template

    def install_bundled(self, directory: Path) -> int:
        """Install new verified packages shipped with an application release."""
        if not directory.exists():
            return 0
        installed = 0
        for package in sorted(directory.glob("*.psfstemplate")):
            try:
                self.install_package(package)
            except FileExistsError:
                continue
            installed += 1
        return installed

    def delete(self, template: Template) -> bool:
        """Remove one exact template version."""
        target = self._version_directory(template)
        if not target.exists():
            return False
        shutil.rmtree(target)
        if target.parent.exists() and not any(target.parent.iterdir()):
            target.parent.rmdir()
        return True

    def source_pdf_path(self, template: Template) -> Path | None:
        """Return the validated locally installed source PDF, if the package contains it."""
        if not template.source_pdf:
            return None
        candidate = self._version_directory(template) / template.source_pdf
        return candidate if candidate.is_file() else None

    def created_date(self, template: Template) -> str:
        """Return metadata date, falling back to the local manifest timestamp."""
        metadata_date = template.metadata.template_created_at[:10]
        if metadata_date:
            return metadata_date
        manifest = self._version_directory(template) / "template.json"
        if not manifest.is_file():
            return "–"
        return datetime.fromtimestamp(manifest.stat().st_mtime).date().isoformat()

    def _version_directory(self, template: Template) -> Path:
        errors = template.validate()
        if errors:
            raise ValueError("; ".join(errors.values()))
        safe_version = template.version.replace("/", "_").replace("\\", "_")
        if safe_version in {"", ".", ".."}:
            raise ValueError("Ungültige Template-Version.")
        return self.directory / template.id / safe_version
