from pdf_smartforms.domain.templates import (
    Rect,
    Template,
    TemplateField,
    TemplateFieldType,
    TemplateMetadata,
    TemplateStatus,
)


def example_template() -> Template:
    return Template(
        id="school.registration",
        name="Schulanmeldung",
        version="1.0.0",
        language="de",
        status=TemplateStatus.LOCAL,
        minimum_app_version="0.3.0",
        source_pdf="form.pdf",
        document_fingerprint="sha256:example",
        metadata=TemplateMetadata(
            institution_name="Theodor-Heuss-Gymnasium",
            institution_category="education",
            city="Wolfsburg",
            document_type="school_book_loan",
            document_published_at="2026-06-17",
            keywords=("Bücherausleihe", "Jahrgang 5"),
        ),
        fields=[
            TemplateField(
                id="participant_first_name",
                label="Vorname",
                type=TemplateFieldType.TEXT,
                page=0,
                rect=Rect(10, 20, 110, 40),
                source="participant.first_name",
                required=True,
                default_value="Mila",
                font_family="Times",
                font_size=8.5,
            )
        ],
    )


def test_template_round_trip() -> None:
    template = example_template()
    restored = Template.from_dict(template.to_dict())
    assert restored == template
    assert restored.validate() == {}


def test_rect_rotates_clockwise() -> None:
    rect = Rect(10, 20, 30, 40)
    assert rect.rotated(100, 200, 90) == Rect(160, 10, 180, 30)
    assert rect.rotated(100, 200, 180) == Rect(70, 160, 90, 180)
    assert rect.rotated(100, 200, 270) == Rect(20, 70, 40, 90)


def test_rect_rejects_invalid_dimensions_and_rotation() -> None:
    try:
        Rect(10, 10, 5, 20)
        raise AssertionError("Invalid rectangle was accepted")
    except ValueError:
        pass
    try:
        Rect(0, 0, 10, 10).rotated(100, 100, 45)
        raise AssertionError("Invalid rotation was accepted")
    except ValueError:
        pass
