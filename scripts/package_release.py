"""Create release metadata, SBOM, ZIP archive and SHA-256 checksums."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from pdf_smartforms.build_info import APP_NAME, EDITION, __version__

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "PDF-SmartForms-Studio"
RELEASE = ROOT / "release"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> None:
    if not DIST.is_dir():
        raise FileNotFoundError("Windows-Build fehlt. Zuerst PyInstaller ausführen.")
    if RELEASE.exists():
        shutil.rmtree(RELEASE)
    RELEASE.mkdir(parents=True)
    archive_base = RELEASE / f"PDF-SmartForms-Studio-{__version__}-Windows"
    archive = Path(shutil.make_archive(str(archive_base), "zip", DIST.parent, DIST.name))
    build_info = {
        "application": APP_NAME,
        "version": __version__,
        "edition": EDITION,
        "commit": git_commit(),
        "built_at": datetime.now(UTC).isoformat(),
        "platform": "Windows x64",
    }
    (RELEASE / "build-info.json").write_text(
        json.dumps(build_info, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    dependencies = ("PyQt6", "PyMuPDF", "Pillow", "platformdirs", "PyInstaller")
    components = [
        {
            "type": "library",
            "name": name,
            "version": package_version(name),
            "purl": f"pkg:pypi/{name.lower()}@{package_version(name)}",
        }
        for name in dependencies
    ]
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid5(NAMESPACE_URL, APP_NAME + __version__)}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(UTC).isoformat(),
            "component": {
                "type": "application",
                "name": APP_NAME,
                "version": __version__,
            },
        },
        "components": components,
    }
    sbom_path = RELEASE / "sbom.cdx.json"
    sbom_path.write_text(json.dumps(sbom, ensure_ascii=False, indent=2), encoding="utf-8")
    checksum_targets = (archive, RELEASE / "build-info.json", sbom_path)
    checksum_lines = [f"{sha256(path)}  {path.name}" for path in checksum_targets]
    (RELEASE / "SHA256SUMS.txt").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    print(f"Releasepaket erstellt: {RELEASE}")


if __name__ == "__main__":
    main()
