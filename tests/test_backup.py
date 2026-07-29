from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from pdf_smartforms.backup.archive import (
    UnsafeBackup,
    create_backup,
    inspect_backup,
    restore_backup,
)
from pdf_smartforms.infrastructure.paths import create_app_paths


def test_backup_roundtrip_skips_existing_files(tmp_path: Path) -> None:
    source = create_app_paths(tmp_path / "source")
    (source.profiles / "family.json").write_text('{"name": "Test"}', encoding="utf-8")
    backup = create_backup(
        tmp_path / "backup.psfsbackup",
        source,
        "0.9.0-beta.1",
        ("profiles",),
    )
    target = create_app_paths(tmp_path / "target")
    info = inspect_backup(backup, target)
    assert info.areas == ("profiles",)
    assert info.files == ("data/profiles/family.json",)
    restore_backup(backup, target)
    assert (target.profiles / "family.json").read_text(encoding="utf-8") == '{"name": "Test"}'

    (target.profiles / "family.json").write_text('{"name": "Keep"}', encoding="utf-8")
    restored = restore_backup(backup, target)
    assert restored.conflicts == ("profiles/family.json",)
    assert (target.profiles / "family.json").read_text(encoding="utf-8") == '{"name": "Keep"}'


def test_backup_rejects_checksum_manipulation(tmp_path: Path) -> None:
    paths = create_app_paths(tmp_path / "data")
    (paths.settings / "app.json").write_text("{}", encoding="utf-8")
    backup = create_backup(tmp_path / "backup.psfsbackup", paths, "test", ("settings",))
    manipulated = tmp_path / "manipulated.psfsbackup"
    with zipfile.ZipFile(backup) as source, zipfile.ZipFile(manipulated, "w") as target:
        for item in source.infolist():
            content = source.read(item.filename)
            if item.filename == "data/settings/app.json":
                content = json.dumps({"changed": True}).encode()
            target.writestr(item, content)
    with pytest.raises(UnsafeBackup, match="Prüfsumme"):
        inspect_backup(manipulated)
