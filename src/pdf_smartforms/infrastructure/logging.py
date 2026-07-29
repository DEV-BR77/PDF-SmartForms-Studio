"""Privacy-preserving application logging."""

from __future__ import annotations

import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_WINDOWS_USER_PATH = re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s]+")


def redact(value: object) -> str:
    """Mask common identifiers before they can enter diagnostic logs."""
    text = str(value)
    text = _EMAIL.sub("[EMAIL]", text)
    return _WINDOWS_USER_PATH.sub(r"C:\\Users\\[USER]", text)


class PrivacyFilter(logging.Filter):
    """Redact message arguments while preserving lazy log formatting."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(redact(arg) for arg in record.args)
        elif isinstance(record.args, dict):
            record.args = {key: redact(value) for key, value in record.args.items()}
        return True


def configure_logging(log_directory: Path) -> None:
    """Configure bounded local logs with no document or profile payloads."""
    log_directory.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        log_directory / "application.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.addFilter(PrivacyFilter())
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    logging.getLogger(__name__).info("Application logging initialized")
