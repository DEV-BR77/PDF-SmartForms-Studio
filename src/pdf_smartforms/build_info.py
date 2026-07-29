"""Build and product metadata shown to users and diagnostics."""

from __future__ import annotations

import os
from dataclasses import dataclass

APP_NAME = "PDF SmartForms Studio"
EDITION = "Community"
__version__ = "0.1.0-alpha.1"
REPOSITORY_URL = "https://github.com/DEV-BR77/PDF-SmartForms-Studio"
COPYRIGHT = "Copyright © Björn Radke"


@dataclass(frozen=True, slots=True)
class BuildInfo:
    """Identifies one concrete application build."""

    version: str
    edition: str
    build: str
    commit: str
    repository_url: str


def current_build_info() -> BuildInfo:
    """Read non-sensitive build metadata supplied by CI or the local environment."""
    return BuildInfo(
        version=__version__,
        edition=EDITION,
        build=os.getenv("PSFS_BUILD_NUMBER", "local"),
        commit=os.getenv("PSFS_GIT_COMMIT", "working-tree"),
        repository_url=REPOSITORY_URL,
    )
