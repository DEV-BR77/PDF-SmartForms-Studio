"""Safe exchange package for another PDF SmartForms user."""

from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from uuid import uuid4

REPOSITORY_URL = "https://github.com/DEV-BR77/PDF-SmartForms-Studio"
ALLOWED_EXTENSIONS = {".pdf", ".psfstemplate", ".json", ".md"}
MAX_PACKAGE_SIZE = 100 * 1024 * 1024


class UnsafeExchangePackage(ValueError):
    """Package violates an exchange security rule."""


@dataclass(frozen=True, slots=True)
class ExchangePackageInfo:
    files: tuple[str, ...]
    checksums_verified: bool


def build_exchange_package(
    target: Path,
    *,
    pdf: Path,
    template_package: Path | None = None,
) -> Path:
    """Create a package with a deliberately blank personal profile."""
    blank_profile = {
        "schema_version": "1.0",
        "profile": {
            "display_name": "",
            "participant_first_name": "",
            "participant_last_name": "",
            "birth_date": None,
            "street": "",
            "postal_code": "",
            "city": "",
            "phone": "",
            "email": "",
            "guardian_1": {},
            "guardian_2": {},
            "custom_fields": [],
        },
    }
    instructions = f"""# Formularpaket öffnen

1. PDF SmartForms Studio aus dem offiziellen Repository installieren:
   {REPOSITORY_URL}
2. Beim Start „Erhaltenes Paket importieren“ wählen.
3. Das leere Profil mit den eigenen Angaben ergänzen.
4. Erkannte Felder und Empfänger vor dem Export prüfen.

Das Paket enthält bewusst keine Namen, Adressen oder Unterschriften.
"""
    files: dict[str, bytes] = {
        pdf.name: pdf.read_bytes(),
        "profile.blank.json": json.dumps(blank_profile, ensure_ascii=False, indent=2).encode(
            "utf-8"
        ),
        "ANLEITUNG.md": instructions.encode("utf-8"),
    }
    if template_package:
        files[template_package.name] = template_package.read_bytes()
    checksums = {name: hashlib.sha256(content).hexdigest() for name, content in files.items()}
    files["checksums.json"] = json.dumps(checksums, indent=2).encode("utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    inspect_exchange_package(target)
    return target


def inspect_exchange_package(path: Path) -> ExchangePackageInfo:
    if path.suffix.casefold() not in {".zip", ".psfspackage"}:
        raise UnsafeExchangePackage("Unbekanntes Paketformat.")
    if not path.exists() or path.stat().st_size > MAX_PACKAGE_SIZE:
        raise UnsafeExchangePackage("Paket fehlt oder überschreitet das Größenlimit.")
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as error:
        raise UnsafeExchangePackage("Paket ist beschädigt.") from error
    with archive:
        members = [item for item in archive.infolist() if not item.is_dir()]
        names: list[str] = []
        for member in members:
            normalized = member.filename.replace("\\", "/")
            pure = PurePosixPath(normalized)
            if pure.is_absolute() or ".." in pure.parts or len(pure.parts) != 1:
                raise UnsafeExchangePackage("Paket enthält einen unsicheren Pfad.")
            if pure.suffix.casefold() not in ALLOWED_EXTENSIONS:
                raise UnsafeExchangePackage(f"Dateityp nicht erlaubt: {pure.suffix}")
            names.append(pure.as_posix())
        required = {"profile.blank.json", "ANLEITUNG.md", "checksums.json"}
        if not required.issubset(names) or not any(name.endswith(".pdf") for name in names):
            raise UnsafeExchangePackage("Paket ist unvollständig.")
        checksums = json.loads(archive.read("checksums.json"))
        for name, expected in checksums.items():
            if name not in names:
                raise UnsafeExchangePackage(f"Prüfsumme verweist auf fehlende Datei: {name}")
            actual = hashlib.sha256(archive.read(name)).hexdigest()
            if actual != expected:
                raise UnsafeExchangePackage(f"Prüfsumme stimmt nicht: {name}")
        profile = json.loads(archive.read("profile.blank.json"))
        profile_text = json.dumps(profile.get("profile", {}), ensure_ascii=False)
        if any(
            value
            for value in profile.get("profile", {}).values()
            if value not in ("", None, [], {})
        ):
            raise UnsafeExchangePackage("Das Austauschprofil enthält persönliche Werte.")
        if "signature" in profile_text.casefold():
            raise UnsafeExchangePackage("Das Austauschprofil enthält eine Signaturreferenz.")
        return ExchangePackageInfo(tuple(sorted(names)), True)


def import_exchange_package(path: Path, target_root: Path) -> Path:
    """Validate first, then extract only root-level approved files."""
    info = inspect_exchange_package(path)
    target = target_root / f"received-{uuid4().hex}"
    target.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(path) as archive:
        for name in info.files:
            (target / name).write_bytes(archive.read(name))
    return target
