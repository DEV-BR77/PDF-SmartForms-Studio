import json
from pathlib import Path

import pytest

from pdf_smartforms.domain.detection import MatchStatus
from pdf_smartforms.domain.field_dictionary import (
    AliasConflict,
    FieldDictionary,
)
from pdf_smartforms.field_dictionary.repository import FieldDictionaryRepository


def test_seed_dictionary_matches_exact_and_fuzzy_labels() -> None:
    dictionary = FieldDictionary.with_seed_data()
    assert dictionary.match("Geburtsdatum")[1] == MatchStatus.MAPPED
    assert dictionary.match("Geburtsdatm")[1] == MatchStatus.UNCERTAIN
    assert dictionary.match("Lieblingsfarbe")[1] == MatchStatus.MISSING


def test_learning_is_explicit_and_rejects_conflicts() -> None:
    dictionary = FieldDictionary.with_seed_data()
    assert dictionary.learn("Name des Sprösslings", "participant.first_name")
    assert not dictionary.learn("Name des Sprösslings", "participant.first_name")
    with pytest.raises(AliasConflict):
        dictionary.learn("Name des Sprösslings", "participant.last_name")


def test_merge_reports_conflicts_without_overwriting() -> None:
    current = FieldDictionary(entries={"participant.first_name": {"kindname"}})
    incoming = FieldDictionary(
        entries={
            "participant.last_name": {"kindname", "familienname neu"},
        }
    )
    report = current.merge(incoming)
    assert report.added == 1
    assert len(report.conflicts) == 1
    assert current.match("kindname")[0] == "participant.first_name"


def test_merge_can_explicitly_replace_conflicting_assignment() -> None:
    current = FieldDictionary(entries={"contact.phone": {"mobil"}})
    incoming = FieldDictionary(entries={"contact.mobile": {"mobil"}})

    report = current.merge(incoming, overwrite_conflicts=True)

    assert report.conflicts == ()
    assert current.match("mobil")[0] == "contact.mobile"


def test_repository_persists_imports_and_exports_without_profile_values(
    tmp_path: Path,
) -> None:
    repository = FieldDictionaryRepository(tmp_path / "dictionary")
    assert repository.learn("Sportler Vorname", "participant.first_name")
    assert repository.load().match("Sportler Vorname")[0] == "participant.first_name"

    exported = tmp_path / "export.json"
    repository.export_to(exported)
    payload = json.loads(exported.read_text(encoding="utf-8"))
    assert "entries" in payload
    assert "profile" not in payload
    assert "values" not in payload

    incoming = tmp_path / "incoming.json"
    incoming.write_text(
        json.dumps(FieldDictionary(entries={"custom.club": {"vereinsname"}}).to_dict()),
        encoding="utf-8",
    )
    report = repository.import_from(incoming)
    assert report.added == 1
    assert repository.load().match("Vereinsname")[0] == "custom.club"


def test_repository_migrates_mobile_away_from_general_phone(tmp_path: Path) -> None:
    repository = FieldDictionaryRepository(tmp_path / "dictionary")
    repository.path.write_text(
        json.dumps(
            FieldDictionary(
                entries={
                    "contact.phone": {"telefon", "mobil"},
                    "contact.mobile": set(),
                }
            ).to_dict()
        ),
        encoding="utf-8",
    )

    dictionary = repository.load()

    assert dictionary.match("mobil")[0] == "contact.mobile"
    assert dictionary.match("telefon")[0] == "contact.phone"


def test_unknown_dictionary_schema_is_rejected() -> None:
    with pytest.raises(ValueError):
        FieldDictionary.from_dict({"schema_version": "99", "language": "de", "entries": {}})


def test_legacy_contact_mobil_source_is_migrated() -> None:
    dictionary = FieldDictionary.from_dict(
        {
            "schema_version": "1.0",
            "language": "de",
            "entries": {"contact.mobil": ["Handynummer"]},
        }
    )

    assert "contact.mobil" not in dictionary.entries
    assert dictionary.match("Handynummer")[0] == "contact.mobile"
