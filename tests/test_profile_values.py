from datetime import date

from pdf_smartforms.domain.profiles import Guardian, Profile
from pdf_smartforms.profiles.values import profile_value


def test_profile_values_are_resolved_for_document_fields() -> None:
    profile = Profile(
        participant_first_name="Mila",
        participant_last_name="Radke",
        birth_date=date(2015, 11, 8),
        postal_code="38440",
        city="Wolfsburg",
        guardian_1=Guardian(first_name="Melanie", last_name="Radke"),
    )

    assert profile_value(profile, "participant.first_name") == "Mila"
    assert profile_value(profile, "participant.birth_date") == "08.11.2015"
    assert profile_value(profile, "guardian.1.last_name") == "Radke"
    assert profile_value(profile, "address.city", "PLZ und Ort") == "38440 Wolfsburg"
