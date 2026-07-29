"""Validate plugin metadata without importing or executing plugin code."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

PLUGIN_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
KNOWN_PERMISSIONS = {
    "document.read",
    "document.write",
    "email.create_draft",
    "network.access",
    "storage.local",
}


class InvalidPluginManifest(ValueError):
    """Plugin metadata is incomplete or requests unknown capabilities."""


@dataclass(frozen=True, slots=True)
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    publisher: str
    minimum_app_version: str
    permissions: tuple[str, ...]


def load_plugin_manifest(path: Path) -> PluginManifest:
    """Load metadata only. Plugin execution is intentionally not implemented."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InvalidPluginManifest("Plugin-Manifest ist nicht lesbar.") from error
    required = ("id", "name", "version", "publisher", "minimum_app_version")
    if any(not isinstance(payload.get(key), str) or not payload[key].strip() for key in required):
        raise InvalidPluginManifest("Plugin-Manifest enthält unvollständige Angaben.")
    plugin_id = payload["id"].strip()
    if not PLUGIN_ID.fullmatch(plugin_id):
        raise InvalidPluginManifest("Plugin-ID ist ungültig.")
    permissions = payload.get("permissions", [])
    if not isinstance(permissions, list) or any(not isinstance(item, str) for item in permissions):
        raise InvalidPluginManifest("Plugin-Berechtigungen sind ungültig.")
    unknown = set(permissions) - KNOWN_PERMISSIONS
    if unknown:
        raise InvalidPluginManifest(
            f"Unbekannte Plugin-Berechtigungen: {', '.join(sorted(unknown))}"
        )
    return PluginManifest(
        plugin_id=plugin_id,
        name=payload["name"].strip(),
        version=payload["version"].strip(),
        publisher=payload["publisher"].strip(),
        minimum_app_version=payload["minimum_app_version"].strip(),
        permissions=tuple(sorted(set(permissions))),
    )


def discover_plugin_manifests(directory: Path) -> tuple[PluginManifest, ...]:
    """Discover valid manifests without loading executable modules."""
    directory.mkdir(parents=True, exist_ok=True)
    manifests: list[PluginManifest] = []
    for path in sorted(directory.glob("*/plugin.json")):
        try:
            manifests.append(load_plugin_manifest(path))
        except InvalidPluginManifest:
            continue
    return tuple(manifests)
