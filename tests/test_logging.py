from pdf_smartforms.infrastructure.logging import redact


def test_redact_masks_email_addresses() -> None:
    assert "person@example.org" not in redact("Mail person@example.org")
    assert "[EMAIL]" in redact("Mail person@example.org")


def test_redact_masks_windows_user_directory() -> None:
    result = redact(r"C:\Users\RealPerson\Documents\form.pdf")
    assert "RealPerson" not in result
    assert r"C:\Users\[USER]" in result
