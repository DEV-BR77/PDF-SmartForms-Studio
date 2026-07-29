"""Secure template package inspection."""

from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from pdf_smartforms.domain.templates import Template

ALLOWED_EXTENSIONS = {".pdf", ".json", ".png", ".jpg", ".jpeg", ".md", ".txt"}
MAX_FILE_SIZE = 25 * 1024 * 1024
MAX_PACKAGE_SIZE = 75 * 1024 * 1024
MAX_FILE_COUNT = 100


class UnsafeTemplatePackage(ValueError):
    """Raised when a package violates an import security rule."""


@dataclass(frozen=True, slots=True)
class InspectedPackage:
    """Validated metadata without extracting the archive."""

    template: Template
    files: tuple[str, ...]
    checksums_verified: bool


def inspect_package(package_path: Path) -> InspectedPackage:
    """Validate archive paths, types, sizes, manifest and optional checksums."""
    if package_path.suffix.casefold() not in {".zip", ".psfstemplate"}:
        raise UnsafeTemplatePackage("Nur ZIP- oder PSFS-Templatepakete werden unterstützt.")
    if package_path.stat().st_size > MAX_PACKAGE_SIZE:
        raise UnsafeTemplatePackage("Templatepaket überschreitet das Größenlimit.")
    try:
        archive = zipfile.ZipFile(package_path)
    except zipfile.BadZipFile as error:
        raise UnsafeTemplatePackage("Templatepaket ist beschädigt.") from error
    with archive:
        members = [member for member in archive.infolist() if not member.is_dir()]
        if not members or len(members) > MAX_FILE_COUNT:
            raise UnsafeTemplatePackage("Unzulässige Anzahl von Paketdateien.")
        normalized_names: list[str] = []
        total_size = 0
        for member in members:
            name = _validate_member(member)
            normalized_names.append(name)
            total_size += member.file_size
        if total_size > MAX_PACKAGE_SIZE:
            raise UnsafeTemplatePackage("Entpackter Paketinhalt überschreitet das Limit.")
        manifest_name = _find_unique(normalized_names, "template.json")
        payload = json.loads(archive.read(manifest_name))
        template = Template.from_dict(payload)
        errors = template.validate()
        if errors:
            raise UnsafeTemplatePackage("; ".join(errors.values()))
        if template.source_pdf not in normalized_names:
            raise UnsafeTemplatePackage("Das im Template genannte Quell-PDF fehlt.")
        checksums_verified = _verify_checksums(archive, normalized_names)
        return InspectedPackage(
            template=template,
            files=tuple(normalized_names),
            checksums_verified=checksums_verified,
        )


def read_validated_files(package_path: Path) -> dict[str, bytes]:
    """Return bytes only after the complete package passes inspection."""
    inspected = inspect_package(package_path)
    with zipfile.ZipFile(package_path) as archive:
        return {name: archive.read(name) for name in inspected.files}


def _validate_member(member: zipfile.ZipInfo) -> str:
    normalized = member.filename.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts:
        raise UnsafeTemplatePackage("Paket enthält einen unsicheren Dateipfad.")
    if len(path.parts) != 1:
        raise UnsafeTemplatePackage("Paketdateien müssen im Paketwurzelverzeichnis liegen.")
    if path.suffix.casefold() not in ALLOWED_EXTENSIONS:
        raise UnsafeTemplatePackage(f"Dateityp nicht erlaubt: {path.suffix or '[ohne Endung]'}")
    if member.file_size > MAX_FILE_SIZE:
        raise UnsafeTemplatePackage(f"Datei überschreitet das Größenlimit: {path.name}")
    return path.as_posix()


def _find_unique(names: list[str], wanted: str) -> str:
    matches = [name for name in names if name.casefold() == wanted.casefold()]
    if len(matches) != 1:
        raise UnsafeTemplatePackage(f"{wanted} fehlt oder ist nicht eindeutig.")
    return matches[0]


def _verify_checksums(archive: zipfile.ZipFile, names: list[str]) -> bool:
    checksum_names = [name for name in names if name.casefold() == "checksums.json"]
    if not checksum_names:
        return False
    try:
        checksums = json.loads(archive.read(checksum_names[0]))
    except json.JSONDecodeError as error:
        raise UnsafeTemplatePackage("Prüfsummendatei ist ungültig.") from error
    for name, expected in checksums.items():
        if name == "checksums.json":
            continue
        if name not in names:
            raise UnsafeTemplatePackage(f"Prüfsumme verweist auf fehlende Datei: {name}")
        actual = hashlib.sha256(archive.read(name)).hexdigest()
        if actual.casefold() != str(expected).casefold():
            raise UnsafeTemplatePackage(f"Prüfsumme stimmt nicht: {name}")
    return True
