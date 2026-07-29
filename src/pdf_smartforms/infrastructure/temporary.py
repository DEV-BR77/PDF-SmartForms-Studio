"""Application-owned temporary workspace with startup cleanup."""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4


def clean_temporary_root(root: Path) -> int:
    """Remove abandoned application workspaces and return their count."""
    root.mkdir(parents=True, exist_ok=True)
    removed = 0
    for child in root.iterdir():
        if not child.name.startswith("psfs-"):
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
        removed += 1
    return removed


@contextmanager
def temporary_workspace(root: Path) -> Iterator[Path]:
    """Yield a private random workspace and remove it even after failures."""
    root.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix=f"psfs-{uuid4().hex[:8]}-", dir=root))
    try:
        yield directory
    finally:
        shutil.rmtree(directory, ignore_errors=True)
