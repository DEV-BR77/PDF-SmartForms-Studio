from pathlib import Path

from pdf_smartforms.infrastructure.temporary import clean_temporary_root, temporary_workspace


def test_temporary_workspace_is_always_removed(tmp_path: Path) -> None:
    root = tmp_path / "temporary"
    with temporary_workspace(root) as workspace:
        assert workspace.is_dir()
        assert workspace.name.startswith("psfs-")
    assert list(root.iterdir()) == []


def test_startup_cleanup_keeps_unrelated_content(tmp_path: Path) -> None:
    (tmp_path / "psfs-abandoned").mkdir()
    (tmp_path / "keep.txt").write_text("keep", encoding="utf-8")
    assert clean_temporary_root(tmp_path) == 1
    assert (tmp_path / "keep.txt").exists()
