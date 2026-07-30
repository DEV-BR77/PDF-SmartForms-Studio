from pdf_smartforms.domain.profiles import CustomField, Profile
from pdf_smartforms.profiles.values import profile_value


def test_resolves_separate_landline_and_mobile_values() -> None:
    profile = Profile(
        participant_first_name="Mila",
        participant_last_name="Beispiel",
        phone="05361 1234",
        mobile="0179 5678",
    )

    assert profile_value(profile, "contact.phone") == "05361 1234"
    assert profile_value(profile, "contact.mobile") == "0179 5678"
    assert profile_value(profile, "participant.name") == "Mila Beispiel"


def test_resolves_custom_field_with_namespaced_or_legacy_key() -> None:
    profile = Profile(
        custom_fields=[
            CustomField(key="custom.club_name", label="Verein", value="TSV Beispiel"),
            CustomField(key="health_insurance", label="Krankenkasse", value="Beispielkasse"),
        ]
    )

    assert profile_value(profile, "custom.club_name") == "TSV Beispiel"
    assert profile_value(profile, "custom.health_insurance") == "Beispielkasse"
