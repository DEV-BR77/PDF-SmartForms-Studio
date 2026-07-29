"""Local application storage paths."""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path

from platformdirs import user_data_path


@dataclass(frozen=True, slots=True)
class AppPaths:
    """Separated storage areas with different protection needs."""

    root: Path
    profiles: Path
    signatures: Path
    templates: Path
    field_dictionary: Path
    distribution_lists: Path
    generated_documents: Path
    backups: Path
    logs: Path
    settings: Path
    temporary: Path


def create_app_paths(root: Path | None = None) -> AppPaths:
    """Create application-owned folders without requiring administrator rights."""
    data_root = root or user_data_path("PDF SmartForms Studio", "Bjoern Radke")
    paths = AppPaths(
        root=data_root,
        profiles=data_root / "profiles",
        signatures=data_root / "signatures",
        templates=data_root / "templates",
        field_dictionary=data_root / "field-dictionary",
        distribution_lists=data_root / "distribution-lists",
        generated_documents=data_root / "generated-documents",
        backups=data_root / "backups",
        logs=data_root / "logs",
        settings=data_root / "settings",
        temporary=data_root / "temporary",
    )
    for descriptor in fields(paths):
        path = getattr(paths, descriptor.name)
        path.mkdir(parents=True, exist_ok=True)
    return paths
