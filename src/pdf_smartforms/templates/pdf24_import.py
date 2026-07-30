"""Import the documented JSON form specification exported by PDF24."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pdf_smartforms.domain.templates import Rect, TemplateFieldType

_TYPE_MAP = {
    "text": TemplateFieldType.TEXT,
    "textarea": TemplateFieldType.MULTILINE,
    "checkbox": TemplateFieldType.CHECKBOX,
    "radio": TemplateFieldType.RADIO,
    "dropdown": TemplateFieldType.CHOICE,
    "listbox": TemplateFieldType.CHOICE,
    "signature": TemplateFieldType.DIGITAL_SIGNATURE,
}


def load_pdf24_form_spec(path: Path) -> list[dict[str, Any]]:
    """Return normalized designer field dictionaries from a PDF24 JSON export."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Die PDF24-Formulardatei ist nicht lesbar.") from error

    if payload.get("settings", {}).get("coordinateOrigin") != "topLeft":
        raise ValueError("Nur PDF24-Exporte mit Koordinatenursprung oben links werden unterstützt.")
    raw_fields = payload.get("fields")
    if not isinstance(raw_fields, list):
        raise ValueError("Die PDF24-Datei enthält keine Feldliste.")

    fields: list[dict[str, Any]] = []
    for index, item in enumerate(raw_fields):
        if not isinstance(item, dict):
            raise ValueError(f"Feld {index + 1} besitzt ein ungültiges Format.")
        field_type = _TYPE_MAP.get(str(item.get("type", "")).casefold())
        rect = item.get("rect")
        if field_type is None or not isinstance(rect, dict):
            raise ValueError(f"Feld {index + 1} verwendet einen nicht unterstützten Feldtyp.")
        try:
            x = float(rect["x"])
            y = float(rect["y"])
            width = float(rect["w"])
            height = float(rect["h"])
            page = int(item.get("page", 1)) - 1
            normalized_rect = Rect(x, y, x + width, y + height)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Feld {index + 1} besitzt ungültige Koordinaten.") from error
        if page < 0:
            raise ValueError(f"Feld {index + 1} besitzt eine ungültige Seitennummer.")
        fields.append(
            {
                "id": str(item.get("id") or f"pdf24-field-{index + 1}"),
                "label": str(item.get("name") or f"Feld {index + 1}"),
                "type": field_type,
                "page": page,
                "rect": normalized_rect,
                "required": bool(item.get("flags", {}).get("required", False)),
            }
        )
    return fields
