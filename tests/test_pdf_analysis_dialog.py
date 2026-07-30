import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pymupdf
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QMessageBox

from pdf_smartforms.domain.profiles import Profile
from pdf_smartforms.field_dictionary.repository import FieldDictionaryRepository
from pdf_smartforms.profiles.repository import ProfileRepository
from pdf_smartforms.signatures.repository import SignatureRepository
from pdf_smartforms.templates.repository import TemplateRepository
from pdf_smartforms.ui.pdf_analysis_dialog import (
    PdfAnalysisDialog,
    SignatureOverlayItem,
    SignaturePlacementState,
)

APP = QApplication.instance() or QApplication([])


def create_form(path: Path) -> None:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((40, 80), "Vorname:")
    document.save(path)
    document.close()


def create_dialog(tmp_path: Path) -> PdfAnalysisDialog:
    pdf = tmp_path / "form.pdf"
    create_form(pdf)
    return PdfAnalysisDialog(
        pdf,
        FieldDictionaryRepository(tmp_path / "dictionary"),
        SignatureRepository(tmp_path / "signatures"),
        ProfileRepository(tmp_path / "profiles"),
        TemplateRepository(tmp_path / "templates"),
    )


def test_analysis_window_has_minimize_and_maximize_buttons(tmp_path: Path) -> None:
    dialog = create_dialog(tmp_path)

    flags = dialog.windowFlags()

    assert flags & Qt.WindowType.WindowMinimizeButtonHint
    assert flags & Qt.WindowType.WindowMaximizeButtonHint


def test_page_is_refitted_and_false_detection_can_be_removed(tmp_path: Path, monkeypatch) -> None:
    dialog = create_dialog(tmp_path)
    dialog.show()
    QApplication.processEvents()

    assert dialog.view.auto_fit
    assert dialog.view.transform().m11() > 0
    assert dialog.field_list.count() == 1

    dialog.field_list.setCurrentRow(0)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    dialog._remove_selected_detection()

    assert dialog.field_list.count() == 0
    assert dialog.analysis.fields == ()


def test_selected_signature_scales_immediately_and_can_be_removed(tmp_path: Path) -> None:
    dialog = create_dialog(tmp_path)
    state = SignaturePlacementState("asset", 0, 100, 100, 0.5)
    item = SignatureOverlayItem(QPixmap(200, 80), state)
    dialog.signature_placements.append(state)
    dialog.scene.addItem(item)
    dialog.signature_items.append(item)
    item.setSelected(True)

    dialog._change_signature_scale(65)

    assert state.scale == 0.65
    assert item.scale() == 0.65

    dialog._remove_selected_signature()

    assert dialog.signature_placements == []


def test_selected_profile_values_are_prepared_for_preview_and_export(tmp_path: Path) -> None:
    profiles = ProfileRepository(tmp_path / "profiles")
    profiles.save(
        Profile(
            display_name="Mila",
            participant_first_name="Mila",
            participant_last_name="Radke",
        )
    )
    pdf = tmp_path / "form.pdf"
    create_form(pdf)
    dialog = PdfAnalysisDialog(
        pdf,
        FieldDictionaryRepository(tmp_path / "dictionary"),
        SignatureRepository(tmp_path / "signatures"),
        profiles,
        TemplateRepository(tmp_path / "templates"),
    )

    texts = dialog._placed_texts()

    assert len(texts) == 1
    assert texts[0].value == "Mila"
