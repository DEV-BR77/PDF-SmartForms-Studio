from pdf_smartforms.domain.safety import SafetyReview


def test_safety_review_warns_about_unresolved_fields_or_missing_recipient() -> None:
    unresolved = SafetyReview("PDF speichern", "form.pdf", 2, 1, 0)
    email = SafetyReview("E-Mail-Entwurf", "form.pdf", 3, 0, 0)
    ready = SafetyReview("E-Mail-Entwurf", "form.pdf", 3, 0, 1, ("test@example.org",))
    assert unresolved.has_warnings
    assert email.has_warnings
    assert not ready.has_warnings
