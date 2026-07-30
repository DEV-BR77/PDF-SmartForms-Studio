from datetime import date

from pdf_smartforms.domain.profiles import (
    CustomField,
    FieldSensitivity,
    Guardian,
    Profile,
)


def test_profile_round_trip_preserves_flexible_fields() -> None:
    profile = Profile(
        display_name="Testprofil",
        participant_first_name="Mila",
        participant_last_name="Beispiel",
        birth_date=date(2015, 11, 8),
        city="Wolfsburg",
        phone="05361 1234",
        mobile="0179 1234",
        guardian_1=Guardian(first_name="Melanie", last_name="Beispiel"),
        custom_fields=[
            CustomField(
                key="health_insurance",
                label="Krankenkasse",
                value="Beispielkasse",
                sensitivity=FieldSensitivity.SENSITIVE,
            )
        ],
    )
    restored = Profile.from_dict(profile.to_dict())
    assert restored == profile
    assert restored.custom_fields[0].sensitivity == FieldSensitivity.SENSITIVE
    assert restored.phone == "05361 1234"
    assert restored.mobile == "0179 1234"


def test_profile_requires_participant_name() -> None:
    errors = Profile().validate()
    assert "participant_first_name" in errors
    assert "participant_last_name" in errors


def test_profile_rejects_duplicate_custom_keys() -> None:
    profile = Profile(
        participant_first_name="Test",
        participant_last_name="Person",
        custom_fields=[
            CustomField(key="club", label="Verein"),
            CustomField(key="club", label="Sportverein"),
        ],
    )
    assert "custom_fields" in profile.validate()


def test_effective_display_name_uses_participant_name() -> None:
    profile = Profile(participant_first_name="Test", participant_last_name="Person")
    assert profile.effective_display_name() == "Test Person"
