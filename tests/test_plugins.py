import json
from pathlib import Path

import pytest

from pdf_smartforms.plugins.manifest import (
    InvalidPluginManifest,
    discover_plugin_manifests,
    load_plugin_manifest,
)


def test_plugin_discovery_reads_metadata_without_executing_code(tmp_path: Path) -> None:
    plugin = tmp_path / "example"
    plugin.mkdir()
    (plugin / "plugin.json").write_text(
        json.dumps(
            {
                "id": "pdfsmartforms.example",
                "name": "Example",
                "version": "1.0.0",
                "publisher": "Test",
                "minimum_app_version": "0.9.0",
                "permissions": ["document.read"],
            }
        ),
        encoding="utf-8",
    )
    (plugin / "plugin.py").write_text("raise RuntimeError('must not execute')", encoding="utf-8")
    manifests = discover_plugin_manifests(tmp_path)
    assert len(manifests) == 1
    assert manifests[0].permissions == ("document.read",)


def test_unknown_plugin_permission_is_rejected(tmp_path: Path) -> None:
    manifest = tmp_path / "plugin.json"
    manifest.write_text(
        json.dumps(
            {
                "id": "unsafe",
                "name": "Unsafe",
                "version": "1",
                "publisher": "Test",
                "minimum_app_version": "0.9",
                "permissions": ["profile.read.sensitive"],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(InvalidPluginManifest, match="Unbekannte"):
        load_plugin_manifest(manifest)
