"""Local distribution-list repository."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from pdf_smartforms.domain.distribution import DistributionList

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DistributionLists = list[DistributionList]


class DistributionListRepository:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "distribution-lists.json"

    def list(self) -> DistributionLists:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return sorted(
            (DistributionList.from_dict(item) for item in payload.get("lists", [])),
            key=lambda item: item.name.casefold(),
        )

    def save(self, distribution_list: DistributionList) -> None:
        if not distribution_list.name.strip():
            raise ValueError("Name der Verteilerliste fehlt.")
        invalid = [item for item in distribution_list.recipients if not _EMAIL.match(item)]
        if invalid:
            raise ValueError(f"Ungültige E-Mail-Adresse: {invalid[0]}")
        lists = [item for item in self.list() if item.id != distribution_list.id]
        distribution_list.recipients = sorted(
            {item.casefold() for item in distribution_list.recipients}
        )
        lists.append(distribution_list)
        self._write(lists)

    def delete(self, list_id: str) -> bool:
        lists = self.list()
        retained = [item for item in lists if item.id != list_id]
        if len(retained) == len(lists):
            return False
        self._write(retained)
        return True

    def _write(self, lists: DistributionLists) -> None:
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "lists": [item.to_dict() for item in lists],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        os.replace(temporary, self.path)
