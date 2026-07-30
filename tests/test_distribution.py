from email import policy
from email.parser import BytesParser
from pathlib import Path

import pymupdf
import pytest
from PIL import Image, ImageDraw

from pdf_smartforms.distribution.document_exporter import export_work_copy
from pdf_smartforms.distribution.email_draft import create_email_draft
from pdf_smartforms.distribution.metadata import clean_document_title, suggest_communication
from pdf_smartforms.distribution.repository import DistributionListRepository
from pdf_smartforms.domain.distribution import DistributionList, PlacedSignature, PlacedText


def create_contact_pdf(path: Path) -> None:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((40, 60), "Anmeldung Sportverein")
    page.insert_text((40, 90), "Kontakt: verein@example.org")
    document.save(path)
    document.close()


def create_signature(path: Path) -> None:
    image = Image.new("RGBA", (220, 80), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.line((20, 50, 190, 30), fill="black", width=4)
    image.save(path)


def test_communication_suggestions_are_local_and_deterministic(tmp_path: Path) -> None:
    pdf = tmp_path / "registration.pdf"
    create_contact_pdf(pdf)
    suggestion = suggest_communication(pdf)
    assert suggestion.title == "Anmeldung Sportverein"
    assert suggestion.recipients == ("verein@example.org",)
    assert "Anmeldung Sportverein" in suggestion.subject


def test_document_title_drops_postal_address_suffix() -> None:
    assert (
        clean_document_title(
            "Bildungszentrum Wolfsburg gGmbH • Postfach 101027 • 38440 Wolfsburg",
            "Anmeldeformular",
        )
        == "Bildungszentrum Wolfsburg gGmbH"
    )


def test_visible_heading_is_preferred_over_internal_metadata(tmp_path: Path) -> None:
    pdf = tmp_path / "form.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((40, 80), "Anmeldung Schulverpflegung", fontsize=18)
    document.set_metadata({"title": "Organisation • Postfach 123"})
    document.save(pdf)
    document.close()

    assert suggest_communication(pdf).title == "Anmeldung Schulverpflegung"


def test_work_copy_embeds_placed_signature(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    signature = tmp_path / "signature.png"
    target = tmp_path / "output.pdf"
    create_contact_pdf(source)
    create_signature(signature)
    export_work_copy(
        source,
        target,
        [PlacedSignature(str(signature), 0, 100, 120, 260, 180)],
    )
    with pymupdf.open(target) as document:
        assert document.load_page(0).get_images()


def test_work_copy_embeds_profile_text(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    target = tmp_path / "output.pdf"
    create_contact_pdf(source)

    export_work_copy(
        source,
        target,
        [],
        [PlacedText("Mila Radke", 0, 100, 120, 300, 145)],
    )

    with pymupdf.open(target) as document:
        assert "Mila Radke" in document.load_page(0).get_text()


def test_email_draft_contains_attachment_but_is_not_sent(tmp_path: Path) -> None:
    attachment = tmp_path / "form.pdf"
    create_contact_pdf(attachment)
    target = tmp_path / "draft.eml"
    create_email_draft(
        target,
        recipients=["recipient@example.org"],
        subject="Formular",
        body="Bitte prüfen.",
        attachments=[attachment],
    )
    message = BytesParser(policy=policy.default).parsebytes(target.read_bytes())
    assert message["To"] == "recipient@example.org"
    assert message["Subject"] == "Formular"
    assert any(part.get_filename() == "form.pdf" for part in message.iter_attachments())


def test_distribution_lists_validate_deduplicate_and_delete(tmp_path: Path) -> None:
    repository = DistributionListRepository(tmp_path / "distribution")
    distribution_list = DistributionList(
        name="Sportverein",
        recipients=["A@example.org", "a@example.org", "b@example.org"],
    )
    repository.save(distribution_list)
    stored = repository.list()[0]
    assert stored.recipients == ["a@example.org", "b@example.org"]
    assert repository.delete(stored.id)


def test_distribution_list_rejects_invalid_email(tmp_path: Path) -> None:
    repository = DistributionListRepository(tmp_path / "distribution")
    with pytest.raises(ValueError):
        repository.save(DistributionList(name="Fehler", recipients=["not-an-email"]))
