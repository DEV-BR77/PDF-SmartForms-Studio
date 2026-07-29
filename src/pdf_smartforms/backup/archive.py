"""Versioned, integrity-checked local backup archives."""

from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from uuid import uuid4

from pdf_smartforms.infrastructure.paths import AppPaths

BACKUP_FORMAT = "pdf-smartforms-backup"
BACKUP_FORMAT_VERSION = "1.0"
MAX_BACKUP_SIZE = 500 * 1024 * 1024
BACKUP_AREAS = (
    "profiles",
    "templates",
    "field_dictionary",
    "distribution_lists",
    "settings",
)


class UnsafeBackup(ValueError):
    """A backup failed structural or integrity validation."""


@dataclass(frozen=True, slots=True)
class BackupInfo:
    created_at: str
    application_version: str
    areas: tuple[str, ...]
    files: tuple[str, ...]
    conflicts: tuple[str, ...] = ()


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def create_backup(
    target: Path,
    paths: AppPaths,
    application_version: str,
    areas: tuple[str, ...] = BACKUP_AREAS,
) -> Path:
    """Create an open ZIP-based backup without sensitive areas by default."""
    unknown = set(areas) - set(BACKUP_AREAS) - {"signatures", "generated_documents"}
    if unknown:
        raise ValueError(f"Unbekannte Sicherungsbereiche: {', '.join(sorted(unknown))}")
    files: dict[str, bytes] = {}
    for area in areas:
        directory = getattr(paths, area)
        for source in sorted(item for item in directory.rglob("*") if item.is_file()):
            relative = source.relative_to(directory).as_posix()
            files[f"data/{area}/{relative}"] = source.read_bytes()
    checksums = {name: _sha256(content) for name, content in files.items()}
    manifest = {
        "format": BACKUP_FORMAT,
        "format_version": BACKUP_FORMAT_VERSION,
        "application_version": application_version,
        "created_at": datetime.now(UTC).isoformat(),
        "areas": list(areas),
        "files": len(files),
        "encrypted": False,
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
        archive.writestr("checksums.json", json.dumps(checksums, indent=2))
        for name, content in files.items():
            archive.writestr(name, content)
    inspect_backup(target, paths)
    return target


def inspect_backup(path: Path, paths: AppPaths | None = None) -> BackupInfo:
    """Validate structure, paths and all checksums before restore."""
    if not path.exists() or path.stat().st_size > MAX_BACKUP_SIZE:
        raise UnsafeBackup("Sicherung fehlt oder überschreitet das Größenlimit.")
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as error:
        raise UnsafeBackup("Sicherung ist beschädigt.") from error
    with archive:
        members = tuple(item for item in archive.infolist() if not item.is_dir())
        if sum(item.file_size for item in members) > MAX_BACKUP_SIZE:
            raise UnsafeBackup("Entpackte Sicherung überschreitet das Größenlimit.")
        names = tuple(item.filename for item in members)
        if "manifest.json" not in names or "checksums.json" not in names:
            raise UnsafeBackup("Manifest oder Prüfsummen fehlen.")
        for name in names:
            pure = PurePosixPath(name.replace("\\", "/"))
            if pure.is_absolute() or ".." in pure.parts:
                raise UnsafeBackup("Sicherung enthält einen unsicheren Pfad.")
        try:
            manifest = json.loads(archive.read("manifest.json"))
            checksums = json.loads(archive.read("checksums.json"))
        except (json.JSONDecodeError, KeyError) as error:
            raise UnsafeBackup("Sicherungsmetadaten sind ungültig.") from error
        if (
            manifest.get("format") != BACKUP_FORMAT
            or manifest.get("format_version") != BACKUP_FORMAT_VERSION
        ):
            raise UnsafeBackup("Sicherungsformat wird nicht unterstützt.")
        areas = tuple(manifest.get("areas", ()))
        if any(not isinstance(area, str) for area in areas):
            raise UnsafeBackup("Sicherungsbereiche sind ungültig.")
        if not set(areas).issubset(set(BACKUP_AREAS) | {"signatures", "generated_documents"}):
            raise UnsafeBackup("Sicherung enthält einen unbekannten Datenbereich.")
        if not isinstance(checksums, dict) or any(
            not isinstance(name, str) or not isinstance(value, str)
            for name, value in checksums.items()
        ):
            raise UnsafeBackup("Prüfsummenliste ist ungültig.")
        for name, expected in checksums.items():
            if name not in names or _sha256(archive.read(name)) != expected:
                raise UnsafeBackup(f"Prüfsumme stimmt nicht: {name}")
        data_files = tuple(sorted(name for name in names if name.startswith("data/")))
        if set(data_files) != set(checksums):
            raise UnsafeBackup("Dateiliste und Prüfsummen stimmen nicht überein.")
        conflicts: list[str] = []
        for name in data_files:
            parts = PurePosixPath(name).parts
            if len(parts) < 3:
                raise UnsafeBackup("Ungültiger Datenpfad in der Sicherung.")
            area, relative = parts[1], Path(*parts[2:])
            if area not in areas:
                raise UnsafeBackup("Datei gehört zu keinem deklarierten Sicherungsbereich.")
            if paths and (getattr(paths, area) / relative).exists():
                conflicts.append("/".join(parts[1:]))
        return BackupInfo(
            created_at=str(manifest.get("created_at", "")),
            application_version=str(manifest.get("application_version", "")),
            areas=areas,
            files=data_files,
            conflicts=tuple(conflicts),
        )


def restore_backup(path: Path, paths: AppPaths, *, replace: bool = False) -> BackupInfo:
    """Restore only validated files; existing files are skipped unless explicitly replaced."""
    info = inspect_backup(path, paths)
    with zipfile.ZipFile(path) as archive:
        for name in info.files:
            parts = PurePosixPath(name).parts
            area = parts[1]
            destination = getattr(paths, area).joinpath(*parts[2:])
            if destination.exists() and not replace:
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(f".{destination.name}.{uuid4().hex}.tmp")
            temporary.write_bytes(archive.read(name))
            temporary.replace(destination)
    return inspect_backup(path, paths)
