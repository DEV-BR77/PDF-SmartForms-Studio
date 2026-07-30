from pathlib import Path

import pymupdf

from pdf_smartforms.pdf.fingerprint import document_fingerprint


def _create_pdf(path: Path, text: str) -> None:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((40, 80), text)
    document.set_metadata({"title": "Testformular", "author": "Test"})
    document.save(path)
    document.close()


def test_equal_visible_documents_have_equal_fingerprints(tmp_path: Path) -> None:
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    _create_pdf(first, "Name:")
    _create_pdf(second, "Name:")

    assert document_fingerprint(first) == document_fingerprint(second)


def test_different_visible_documents_have_different_fingerprints(tmp_path: Path) -> None:
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    _create_pdf(first, "Name:")
    _create_pdf(second, "Geburtsdatum:")

    assert document_fingerprint(first) != document_fingerprint(second)


def test_widget_values_do_not_change_document_fingerprint(tmp_path: Path) -> None:
    original = tmp_path / "original.pdf"
    with_widget = tmp_path / "with-widget.pdf"
    _create_pdf(original, "Name:")
    document = pymupdf.open(original)
    page = document[0]
    widget = pymupdf.Widget()
    widget.field_name = "name"
    widget.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    widget.rect = pymupdf.Rect(100, 60, 220, 90)
    widget.field_value = "Mila"
    page.add_widget(widget)
    document.save(with_widget)
    document.close()

    assert document_fingerprint(original) == document_fingerprint(with_widget)
