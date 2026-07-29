"""Application entry point."""

from __future__ import annotations

import sys

from pdf_smartforms.application.bootstrap import build_runtime


def main() -> int:
    """Start the desktop application."""
    runtime = build_runtime()
    return runtime.run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
