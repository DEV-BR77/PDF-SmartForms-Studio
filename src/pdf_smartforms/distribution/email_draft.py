"""RFC-compliant local EML draft creation."""

from __future__ import annotations

import mimetypes
from email.message import EmailMessage
from pathlib import Path


def create_email_draft(
    target: Path,
    *,
    recipients: list[str],
    subject: str,
    body: str,
    attachments: list[Path],
) -> Path:
    """Create, but never send, an email draft."""
    message = EmailMessage()
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(body)
    for attachment in attachments:
        mime, _ = mimetypes.guess_type(attachment.name)
        main_type, sub_type = (mime or "application/octet-stream").split("/", 1)
        message.add_attachment(
            attachment.read_bytes(),
            maintype=main_type,
            subtype=sub_type,
            filename=attachment.name,
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(message.as_bytes())
    return target
