from pathlib import Path

import pymupdf
import pytest

from pdf_smartforms.domain.detection import MatchStatus
from pdf_smartforms.domain.field_dictionary import FieldDictionary
from pdf_smartforms.domain.templates import TemplateFieldType
from pdf_smartforms.pdf.analyzer import PdfAnalysisError, analyze_pdf, match_label


def create_acroform(path: Path) -> None:
    document = pymupdf.open()
    page = document.new_page()
    widget = pymupdf.Widget()
    widget.field_name = "participant_first_name"
    widget.field_label = "Vorname Kind"
    widget.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    widget.rect = pymupdf.Rect(100, 100, 300, 125)
    page.add_widget(widget)
    document.set_metadata({"title": "Testanmeldung"})
    document.save(path)
    document.close()


def create_flat_form(path: Path) -> None:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((40, 80), "Vorname:")
    page.insert_text((40, 120), "Krankenkasse:")
    document.save(path)
    document.close()


def test_acroform_fields_are_detected(tmp_path: Path) -> None:
    path = tmp_path / "acroform.pdf"
    create_acroform(path)
    result = analyze_pdf(path)
    assert result.title == "Testanmeldung"
    assert len(result.fields) == 1
    assert result.fields[0].origin == "AcroForm"
    assert result.fields[0].status == MatchStatus.MAPPED
    assert result.fields[0].source == "participant.first_name"


def test_flat_labels_include_mapped_and_missing_fields(tmp_path: Path) -> None:
    path = tmp_path / "flat.pdf"
    create_flat_form(path)
    result = analyze_pdf(path)
    statuses = {field.label.casefold(): field.status for field in result.fields}
    assert statuses["vorname"] == MatchStatus.MAPPED
    assert statuses["krankenkasse"] == MatchStatus.MISSING


def test_small_footer_and_legal_prose_are_not_detected_as_fields(tmp_path: Path) -> None:
    path = tmp_path / "footer.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((40, 80), "Vorname:", fontsize=11)
    page.insert_text(
        (40, 160),
        "Datenschutz: Hinweise zum Datum und zur E-Mail finden Sie im Rechtstext.",
        fontsize=7,
    )
    page.insert_text((40, 800), "E-Mail: footer@example.org", fontsize=6)
    document.save(path)
    document.close()

    result = analyze_pdf(path)

    assert [field.label.casefold() for field in result.fields] == ["vorname"]


def test_label_matching_distinguishes_exact_uncertain_and_missing() -> None:
    assert match_label("Geburtsdatum")[1] == MatchStatus.MAPPED
    assert match_label("Geburtsdatm")[1] == MatchStatus.UNCERTAIN
    assert match_label("Lieblingsfarbe")[1] == MatchStatus.MISSING


def test_analyzer_uses_learned_aliases(tmp_path: Path) -> None:
    path = tmp_path / "learned.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((40, 80), "Sportlername:")
    document.save(path)
    document.close()
    dictionary = FieldDictionary.with_seed_data()
    dictionary.learn("Sportlername", "participant.first_name")
    result = analyze_pdf(path, dictionary)
    assert result.fields[0].source == "participant.first_name"
    assert result.fields[0].status == MatchStatus.MAPPED


def test_date_field_type_is_inferred(tmp_path: Path) -> None:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((40, 80), "Geburtsdatum:")
    path = tmp_path / "date.pdf"
    document.save(path)
    document.close()
    result = analyze_pdf(path)
    assert result.fields[0].type == TemplateFieldType.DATE


def test_non_pdf_and_corrupt_pdf_are_rejected(tmp_path: Path) -> None:
    text = tmp_path / "document.txt"
    text.write_text("not a pdf", encoding="utf-8")
    with pytest.raises(PdfAnalysisError):
        analyze_pdf(text)
    corrupt = tmp_path / "broken.pdf"
    corrupt.write_bytes(b"not a pdf")
    with pytest.raises(PdfAnalysisError):
        analyze_pdf(corrupt)
