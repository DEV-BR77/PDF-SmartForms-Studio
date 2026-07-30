import hashlib
import json
from pathlib import Path

from pdf_smartforms.domain.templates import Template, TemplateStatus
from pdf_smartforms.templates import catalog
from pdf_smartforms.templates.catalog import TemplateCatalogClient
from pdf_smartforms.templates.package_builder import build_template_package
from pdf_smartforms.templates.repository import TemplateRepository


def test_catalog_reports_and_installs_only_missing_versions(tmp_path: Path, monkeypatch) -> None:
    source_pdf = tmp_path / "form.pdf"
    source_pdf.write_bytes(b"%PDF-1.4\n")
    template = Template(
        id="school.registration",
        name="Schulanmeldung",
        version="1.0.0",
        language="de",
        status=TemplateStatus.LOCAL,
        minimum_app_version="1.0.0",
        source_pdf=source_pdf.name,
        document_fingerprint="sha256:example",
    )
    package = build_template_package(
        template,
        source_pdf,
        tmp_path / "template.psfstemplate",
    )
    package_bytes = package.read_bytes()
    catalog_bytes = json.dumps(
        {
            "templates": [
                {
                    "id": "school.registration",
                    "version": "1.0.0",
                    "download_url": "https://example.test/template.psfstemplate",
                    "sha256": hashlib.sha256(package_bytes).hexdigest(),
                }
            ]
        }
    ).encode()

    def fake_download(url: str, _maximum_size: int) -> bytes:
        return package_bytes if url.endswith(".psfstemplate") else catalog_bytes

    monkeypatch.setattr(catalog, "_download", fake_download)
    repository = TemplateRepository(tmp_path / "installed")
    client = TemplateCatalogClient("https://example.test/catalog.json")

    updates = client.available_updates(repository)
    assert len(updates) == 1
    assert client.install_updates(updates, repository) == 1
    assert client.available_updates(repository) == []
