import json
import zipfile
from pathlib import Path

import pymupdf
import pytest

from pdf_smartforms.distribution.exchange_package import (
    UnsafeExchangePackage,
    build_exchange_package,
    import_exchange_package,
    inspect_exchange_package,
)


def create_pdf(path: Path) -> None:
    document = pymupdf.open()
    document.new_page()
    document.save(path)
    document.close()


def test_exchange_package_contains_only_blank_profile_and_guidance(
    tmp_path: Path,
) -> None:
    pdf = tmp_path / "form.pdf"
    create_pdf(pdf)
    target = tmp_path / "form.psfspackage"
    build_exchange_package(target, pdf=pdf)
    info = inspect_exchange_package(target)
    assert info.checksums_verified
    assert "ANLEITUNG.md" in info.files
    imported = import_exchange_package(target, tmp_path / "received")
    assert (imported / "form.pdf").exists()
    with zipfile.ZipFile(target) as archive:
        profile = json.loads(archive.read("profile.blank.json"))
        assert profile["profile"]["participant_first_name"] == ""
        assert "github.com/DEV-BR77/PDF-SmartForms-Studio" in archive.read("ANLEITUNG.md").decode()


def test_exchange_package_blocks_path_traversal(tmp_path: Path) -> None:
    target = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("../outside.json", "{}")
    with pytest.raises(UnsafeExchangePackage):
        inspect_exchange_package(target)
