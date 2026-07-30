"""Local field dictionary and matching rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any

from pdf_smartforms.domain.detection import MatchStatus

_NORMALIZE = re.compile(r"[^a-z0-9äöüß]+")

SEED_ALIASES: dict[str, tuple[str, ...]] = {
    "participant.first_name": (
        "participant first name",
        "vorname kind",
        "vorname schüler",
        "vorname teilnehmer",
        "vorname",
    ),
    "participant.last_name": (
        "participant last name",
        "nachname kind",
        "nachname schüler",
        "familienname",
        "nachname",
    ),
    "participant.birth_date": ("geburtsdatum", "geboren am"),
    "address.street": ("straße", "strasse", "anschrift"),
    "address.postal_code": ("postleitzahl", "plz"),
    "address.city": ("wohnort", "ort"),
    "contact.phone": ("telefonnummer", "telefon", "mobil"),
    "contact.email": ("e-mail", "email", "mailadresse"),
    "guardian.1.first_name": (
        "vorname erziehungsberechtigter",
        "vorname erziehungsberechtigte person",
        "vorname sorgeberechtigte person",
    ),
    "guardian.1.last_name": (
        "nachname erziehungsberechtigter",
        "nachname erziehungsberechtigte person",
        "nachname sorgeberechtigte person",
    ),
    "signature.date": ("unterschriftsdatum", "datum"),
    "signature.place": ("ort der unterschrift",),
}

SOURCE_LABELS: dict[str, str] = {
    "participant.first_name": "Vorname Kind / teilnehmende Person",
    "participant.last_name": "Nachname Kind / teilnehmende Person",
    "participant.birth_date": "Geburtsdatum",
    "address.street": "Straße",
    "address.postal_code": "PLZ",
    "address.city": "Ort",
    "contact.phone": "Telefon",
    "contact.email": "E-Mail",
    "guardian.1.first_name": "Vorname erziehungsberechtigte Person 1",
    "guardian.1.last_name": "Nachname erziehungsberechtigte Person 1",
    "signature.date": "Unterschriftsdatum",
    "signature.place": "Unterschriftsort",
}


def normalize_label(value: str) -> str:
    return _NORMALIZE.sub(" ", value.casefold()).strip()


class AliasConflict(ValueError):
    """One alias is already assigned to another source."""


@dataclass(frozen=True, slots=True)
class ImportReport:
    added: int
    duplicates: int
    conflicts: tuple[str, ...]


@dataclass(slots=True)
class FieldDictionary:
    """Only aliases and source keys; never profile values."""

    language: str = "de"
    entries: dict[str, set[str]] = field(default_factory=dict)

    @classmethod
    def with_seed_data(cls) -> FieldDictionary:
        return cls(entries={source: set(aliases) for source, aliases in SEED_ALIASES.items()})

    def sources(self) -> tuple[str, ...]:
        return tuple(sorted(self.entries))

    def learn(self, alias: str, source: str) -> bool:
        normalized = normalize_label(alias)
        if not normalized:
            raise ValueError("Leerer Feldalias kann nicht gelernt werden.")
        for existing_source, aliases in self.entries.items():
            if normalized in aliases and existing_source != source:
                raise AliasConflict(f"„{normalized}“ ist bereits „{existing_source}“ zugeordnet.")
        target = self.entries.setdefault(source, set())
        before = len(target)
        target.add(normalized)
        return len(target) != before

    def match(self, label: str) -> tuple[str | None, MatchStatus, float]:
        normalized = normalize_label(label)
        if not normalized:
            return None, MatchStatus.MISSING, 0.0
        for source, aliases in self.entries.items():
            if normalized in aliases:
                return source, MatchStatus.MAPPED, 1.0
        best_source: str | None = None
        best_score = 0.0
        for source, aliases in self.entries.items():
            if not aliases:
                continue
            score = max(SequenceMatcher(None, normalized, alias).ratio() for alias in aliases)
            if score > best_score:
                best_source, best_score = source, score
        if best_score >= 0.72:
            return best_source, MatchStatus.UNCERTAIN, round(best_score, 2)
        return None, MatchStatus.MISSING, round(best_score, 2)

    def merge(self, incoming: FieldDictionary) -> ImportReport:
        added = 0
        duplicates = 0
        conflicts: list[str] = []
        for source, aliases in incoming.entries.items():
            for alias in aliases:
                try:
                    if self.learn(alias, source):
                        added += 1
                    else:
                        duplicates += 1
                except AliasConflict as error:
                    conflicts.append(str(error))
        return ImportReport(added, duplicates, tuple(sorted(conflicts)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "language": self.language,
            "entries": {
                source: sorted(aliases) for source, aliases in sorted(self.entries.items())
            },
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> FieldDictionary:
        if payload.get("schema_version") != "1.0":
            raise ValueError("Nicht unterstützte Feldlexikon-Version.")
        entries = {
            str(source): {normalize_label(str(alias)) for alias in aliases}
            for source, aliases in payload.get("entries", {}).items()
        }
        return cls(language=str(payload.get("language", "de")), entries=entries)
