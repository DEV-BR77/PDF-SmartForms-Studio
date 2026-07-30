"""Atomic JSON storage for the local field dictionary."""

from __future__ import annotations

import json
import os
from pathlib import Path

from pdf_smartforms.domain.field_dictionary import FieldDictionary, ImportReport


class FieldDictionaryRepository:
    """Persist aliases without storing profile values."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "field-dictionary.de.json"

    def load(self) -> FieldDictionary:
        if not self.path.exists():
            dictionary = FieldDictionary.with_seed_data()
            self.save(dictionary)
            return dictionary
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        dictionary = FieldDictionary.from_dict(payload)
        report = dictionary.merge(FieldDictionary.with_seed_data())
        migrated = False
        for alias in ("mobil", "mobiltelefon", "handy", "handynummer"):
            migrated = dictionary.reassign(alias, "contact.mobile") or migrated
        if report.added or migrated:
            self.save(dictionary)
        return dictionary

    def save(self, dictionary: FieldDictionary) -> None:
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(dictionary.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(temporary, self.path)

    def learn(self, alias: str, source: str) -> bool:
        dictionary = self.load()
        changed = dictionary.learn(alias, source)
        if changed:
            self.save(dictionary)
        return changed

    def export_to(self, target: Path) -> None:
        target.write_text(
            json.dumps(self.load().to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def import_from(self, source: Path, *, overwrite_conflicts: bool = False) -> ImportReport:
        incoming = FieldDictionary.from_dict(json.loads(source.read_text(encoding="utf-8")))
        current = self.load()
        report = current.merge(incoming, overwrite_conflicts=overwrite_conflicts)
        self.save(current)
        return report
