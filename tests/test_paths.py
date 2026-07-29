from dataclasses import fields
from pathlib import Path

from pdf_smartforms.infrastructure.paths import create_app_paths


def test_all_application_paths_are_created(tmp_path: Path) -> None:
    paths = create_app_paths(tmp_path / "data")
    assert paths.root.is_dir()
    assert paths.profiles.is_dir()
    assert paths.signatures.is_dir()
    assert paths.temporary.is_dir()
    values = [getattr(paths, descriptor.name) for descriptor in fields(paths)]
    assert len(set(values)) == len(values)
