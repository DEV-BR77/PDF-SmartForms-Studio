from pathlib import Path

import pytest

from pdf_smartforms.domain.profiles import Profile
from pdf_smartforms.profiles.repository import ProfileRepository


def valid_profile(name: str = "Test") -> Profile:
    return Profile(
        display_name=name,
        participant_first_name=name,
        participant_last_name="Person",
    )


def test_repository_saves_lists_gets_and_deletes(tmp_path: Path) -> None:
    repository = ProfileRepository(tmp_path / "profiles")
    profile = valid_profile()
    repository.save(profile)

    assert repository.list() == [profile]
    assert repository.get(profile.id) == profile
    assert repository.delete(profile.id)
    assert repository.get(profile.id) is None
    assert not repository.delete(profile.id)


def test_repository_does_not_overwrite_valid_profiles_with_invalid_data(
    tmp_path: Path,
) -> None:
    repository = ProfileRepository(tmp_path / "profiles")
    profile = valid_profile()
    repository.save(profile)
    profile.participant_first_name = ""

    with pytest.raises(ValueError):
        repository.save(profile)

    assert repository.get(profile.id) is not None


def test_repository_rejects_unsafe_profile_identifier(tmp_path: Path) -> None:
    repository = ProfileRepository(tmp_path / "profiles")
    with pytest.raises(ValueError):
        repository.get("../../outside")


def test_repository_skips_corrupt_json(tmp_path: Path) -> None:
    repository = ProfileRepository(tmp_path / "profiles")
    (repository.directory / "broken.json").write_text("{", encoding="utf-8")
    assert repository.list() == []
