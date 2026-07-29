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


def test_unknown_dictionary_schema_is_rejected() -> None:
    with pytest.raises(ValueError):
        FieldDictionary.from_dict({"schema_version": "99", "language": "de", "entries": {}})
