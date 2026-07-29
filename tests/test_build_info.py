from pdf_smartforms.build_info import current_build_info


def test_build_info_has_required_support_fields() -> None:
    info = current_build_info()
    assert info.version
    assert info.edition == "Community"
    assert info.build
    assert info.commit
    assert info.repository_url.startswith("https://github.com/")
