"""Local JSON profile repository."""

from __future__ import annotations

import json
import os
from pathlib import Path

from pdf_smartforms.domain.profiles import Profile


class ProfileRepository:
    """Store one profile per JSON file with atomic replacement."""

    SCHEMA_VERSION = "1.0"

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[Profile]:
        """Return valid profiles sorted for presentation."""
        profiles: list[Profile] = []
        for path in self.directory.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                profiles.append(Profile.from_dict(payload["profile"]))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue
        return sorted(profiles, key=lambda item: item.effective_display_name().casefold())

    def get(self, profile_id: str) -> Profile | None:
        """Load one profile by opaque identifier."""
        path = self._path(profile_id)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return Profile.from_dict(payload["profile"])

    def save(self, profile: Profile) -> None:
        """Validate and atomically write a profile."""
        errors = profile.validate()
        if errors:
            raise ValueError("; ".join(errors.values()))
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "profile": profile.to_dict(),
        }
        target = self._path(profile.id)
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(temporary, target)

    def delete(self, profile_id: str) -> bool:
        """Delete exactly one profile, returning whether it existed."""
        target = self._path(profile_id)
        if not target.exists():
            return False
        target.unlink()
        return True

    def _path(self, profile_id: str) -> Path:
        if not profile_id or any(character not in "0123456789abcdef-" for character in profile_id):
            raise ValueError("Ungültige Profil-ID.")
        return self.directory / f"{profile_id}.json"
