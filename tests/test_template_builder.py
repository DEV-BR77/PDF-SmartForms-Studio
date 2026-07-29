from pathlib import Path

import pymupdf

from pdf_smartforms.templates.package_builder import build_template_package
from pdf_smartforms.templates.package_importer import inspect_package
from pdf_smartforms.templates.repository import TemplateRepository
from tests.test_templates import example_template


def create_pdf(path: Path) -> None:
    document = pymupdf.open()
    document.new_page()
    document.save(path)
    document.close()


def test_builder_creates_self_validating_installable_package(tmp_path: Path) -> None:
    source = tmp_path / "form.pdf"
    create_pdf(source)
    template = example_template()
    target = tmp_path / "school.psfstemplate"

    build_template_package(template, source, target)
    inspected = inspect_package(target)
    assert inspected.checksums_verified
    assert inspected.template == template

    repository = TemplateRepository(tmp_path / "templates")
    repository.install_package(target)
    assert repository.list() == [template]


def test_builder_rejects_mismatched_pdf_name(tmp_path: Path) -> None:
    source = tmp_path / "different.pdf"
    create_pdf(source)
    template = example_template()
    try:
        build_template_package(template, source, tmp_path / "out.psfstemplate")
        raise AssertionError("Mismatched PDF name was accepted")
    except ValueError:
        pass
