from __future__ import annotations

import ast
from pathlib import Path


def test_domain_does_not_import_ui_or_infrastructure() -> None:
    domain = Path("src/pdf_smartforms/domain")
    forbidden = ("pdf_smartforms.ui", "pdf_smartforms.infrastructure", "PyQt6")
    for source_file in domain.rglob("*.py"):
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        imports += [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        ]
        assert not any(item.startswith(forbidden) for item in imports)
