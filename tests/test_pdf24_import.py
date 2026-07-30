import json
from pathlib import Path

import pytest

from pdf_smartforms.domain.templates import TemplateFieldType
from pdf_smartforms.templates.pdf24_import import load_pdf24_form_spec


def test_imports_pdf24_fields_with_top_left_coordinates(tmp_path: Path) -> None:
    source = tmp_path / "form.json"
    source.write_text(
        json.dumps(
            {
                "settings": {"coordinateOrigin": "topLeft"},
                "fields": [
                    {
                        "id": "pdfFormField-0",
                        "page": 1,
                        "type": "text",
                        "name": "Vorname",
                        "rect": {"x": 10, "y": 20, "w": 100, "h": 15},
                        "flags": {"required": True},
                    },
                    {
                        "id": "pdfFormField-1",
                        "page": 2,
                        "type": "signature",
                        "name": "Unterschrift",
                        "rect": {"x": 30, "y": 40, "w": 120, "h": 20},
                        "flags": {},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    fields = load_pdf24_form_spec(source)

    assert fields[0]["page"] == 0
    assert fields[0]["type"] is TemplateFieldType.TEXT
    assert fields[0]["rect"].x1 == 110
    assert fields[0]["required"] is True
    assert fields[1]["page"] == 1
    assert fields[1]["type"] is TemplateFieldType.DIGITAL_SIGNATURE


def test_rejects_unknown_coordinate_origin(tmp_path: Path) -> None:
    source = tmp_path / "form.json"
    source.write_text(
        json.dumps({"settings": {"coordinateOrigin": "bottomLeft"}, "fields": []}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="oben links"):
        load_pdf24_form_spec(source)
