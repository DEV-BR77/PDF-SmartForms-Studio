"""Resolve reusable profile values for detected field sources."""

from __future__ import annotations

from pdf_smartforms.domain.profiles import Profile


def profile_value(profile: Profile | None, source: str | None, label: str = "") -> str:
    if profile is None or source is None:
        return ""
    values = {
        "participant.first_name": profile.participant_first_name,
        "participant.last_name": profile.participant_last_name,
        "participant.birth_date": (
            profile.birth_date.strftime("%d.%m.%Y") if profile.birth_date else ""
        ),
        "address.street": profile.street,
        "address.postal_code": profile.postal_code,
        "address.city": profile.city,
        "contact.phone": profile.phone,
        "contact.email": profile.email,
        "guardian.1.first_name": profile.guardian_1.first_name,
        "guardian.1.last_name": profile.guardian_1.last_name,
        "signature.place": profile.city,
    }
    for custom in profile.custom_fields:
        values[custom.key] = custom.value
    if "plz" in label.casefold() and "ort" in label.casefold():
        return f"{profile.postal_code} {profile.city}".strip()
    return values.get(source, "").strip()
