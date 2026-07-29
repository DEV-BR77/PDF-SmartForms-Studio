from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from pdf_smartforms.templates.package_importer import (
    UnsafeTemplatePackage,
    inspect_package,
)
from pdf_smartforms.templates.repository import TemplateRepository
from tests.test_templates import example_template


def write_package(
    path: Path,
    *,
    bad_checksum: bool = False,
    extra_name: str | None = None,
) -> None:
    template_json = json.dumps(example_template().to_dict()).encode()
    pdf = b"%PDF-1.4\n%%EOF"
    checksums = {
        "template.json": hashlib.sha256(template_json).hexdigest(),
        "form.pdf": "0" * 64 if bad_checksum else hashlib.sha256(pdf).hexdigest(),
    }
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("template.json", template_json)
        archive.writestr("form.pdf", pdf)
        archive.writestr("checksums.json", json.dumps(checksums))
        if extra_name:
            archive.writestr(extra_name, b"blocked")


def test_package_is_inspected_and_installed(tmp_path: Path) -> None:
    package = tmp_path / "template.psfstemplate"
    write_package(package)
    inspected = inspect_package(package)
    assert inspected.checksums_verified
    repository = TemplateRepository(tmp_path / "installed")
    installed = repository.install_package(package)
    assert repository.list() == [installed]
    assert repository.delete(installed)


@pytest.mark.parametrize("extra_name", ["../outside.json", "script.exe", "folder/nested.json"])
def test_package_blocks_unsafe_members(tmp_path: Path, extra_name: str) -> None:
    package = tmp_path / "unsafe.zip"
    write_package(package, extra_name=extra_name)
    with pytest.raises(UnsafeTemplatePackage):
        inspect_package(package)


def test_package_blocks_wrong_checksum(tmp_path: Path) -> None:
    package = tmp_path / "bad.zip"
    write_package(package, bad_checksum=True)
    with pytest.raises(UnsafeTemplatePackage):
        inspect_package(package)


def test_repository_does_not_overwrite_installed_version(tmp_path: Path) -> None:
    package = tmp_path / "template.zip"
    write_package(package)
    repository = TemplateRepository(tmp_path / "installed")
    repository.install_package(package)
    with pytest.raises(FileExistsError):
        repository.install_package(package)
