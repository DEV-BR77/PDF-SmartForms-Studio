"""Optional, integrity-checked template catalog updates."""

from __future__ import annotations

import hashlib
import json
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pdf_smartforms.templates.package_importer import inspect_package
from pdf_smartforms.templates.repository import TemplateRepository

DEFAULT_CATALOG_URL = (
    "https://raw.githubusercontent.com/DEV-BR77/" "PDF-SmartForms-Templates/main/catalog.json"
)
MAX_CATALOG_SIZE = 2 * 1024 * 1024
MAX_TEMPLATE_SIZE = 75 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    id: str
    version: str
    download_url: str
    sha256: str


class TemplateCatalogClient:
    """Fetch public metadata without credentials and install only on request."""

    def __init__(self, catalog_url: str = DEFAULT_CATALOG_URL) -> None:
        self.catalog_url = catalog_url

    def available_updates(self, repository: TemplateRepository) -> list[CatalogEntry]:
        payload = _download(self.catalog_url, MAX_CATALOG_SIZE)
        try:
            document: dict[str, Any] = json.loads(payload)
        except json.JSONDecodeError as error:
            raise ValueError("Der Vorlagenkatalog ist ungültig.") from error
        installed = {(item.id, item.version) for item in repository.list()}
        entries: list[CatalogEntry] = []
        for raw in document.get("templates", []):
            if not isinstance(raw, dict):
                continue
            entry = CatalogEntry(
                id=str(raw.get("id", "")).strip(),
                version=str(raw.get("version", "")).strip(),
                download_url=str(raw.get("download_url", "")).strip(),
                sha256=str(raw.get("sha256", "")).strip().casefold(),
            )
            if (
                entry.id
                and entry.version
                and entry.download_url.startswith("https://")
                and len(entry.sha256) == 64
                and (entry.id, entry.version) not in installed
            ):
                entries.append(entry)
        return entries

    def install_updates(
        self,
        entries: list[CatalogEntry],
        repository: TemplateRepository,
    ) -> int:
        installed = 0
        with tempfile.TemporaryDirectory(prefix="psfs-catalog-") as temporary:
            directory = Path(temporary)
            for index, entry in enumerate(entries):
                content = _download(entry.download_url, MAX_TEMPLATE_SIZE)
                if hashlib.sha256(content).hexdigest() != entry.sha256:
                    raise ValueError(f"Prüfsumme der Vorlage {entry.id} stimmt nicht.")
                package = directory / f"template-{index}.psfstemplate"
                package.write_bytes(content)
                template = inspect_package(package).template
                if template.id != entry.id or template.version != entry.version:
                    raise ValueError(f"Katalogdaten der Vorlage {entry.id} stimmen nicht.")
                repository.install_package(package)
                installed += 1
        return installed


def _download(url: str, maximum_size: int) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "PDF-SmartForms-Studio"},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:  # noqa: S310
            length = int(response.headers.get("Content-Length", "0") or 0)
            if length > maximum_size:
                raise ValueError("Download überschreitet das Größenlimit.")
            content = bytes(response.read(maximum_size + 1))
    except OSError as error:
        raise ValueError("Vorlagenkatalog ist derzeit nicht erreichbar.") from error
    if len(content) > maximum_size:
        raise ValueError("Download überschreitet das Größenlimit.")
    return content
