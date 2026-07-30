import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pymupdf
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QMessageBox

from pdf_smartforms.domain.profiles import Profile
from pdf_smartforms.domain.templates import TemplateFieldType
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


def test_radio_can_become_template_only_form_question(tmp_path: Path) -> None:
    dialog = create_dialog(tmp_path)
    original = dialog.analysis.fields[0]
    radio = original.__class__(
        id=original.id,
        label="Name Schüler/-in – Ja",
        type=TemplateFieldType.RADIO,
        page=original.page,
        rect=original.rect,
        source="participant.name",
        status=original.status,
        confidence=original.confidence,
        origin=original.origin,
        option_value="Ja",
    )
    dialog.analysis = dialog.analysis.__class__(
        dialog.analysis.title,
        dialog.analysis.page_count,
        (radio,),
        dialog.analysis.warnings,
    )
    dialog._populate_field_list()
    dialog.field_list.setCurrentRow(0)
    dialog.form_question.setText("Entgeltliche Lernmittelausleihe")
    dialog.form_group.setText("lernmittel_entgeltliche_ausleihe")
    dialog.form_option.setText("Ja")

    dialog._apply_form_mapping()

    mapped = dialog.analysis.fields[0]
    assert mapped.source == "form.lernmittel_entgeltliche_ausleihe"
    assert mapped.option_value == "Ja"
    assert mapped.label == "Entgeltliche Lernmittelausleihe – Ja"


def test_mapping_can_be_cleared_without_removing_detection(tmp_path: Path) -> None:
    dialog = create_dialog(tmp_path)
    dialog.field_list.setCurrentRow(0)

    dialog._clear_selected_mapping()

    assert len(dialog.analysis.fields) == 1
    assert dialog.analysis.fields[0].source is None
