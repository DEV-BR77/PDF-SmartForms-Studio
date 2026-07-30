import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pymupdf
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox

from pdf_smartforms.field_dictionary.repository import FieldDictionaryRepository
from pdf_smartforms.signatures.repository import SignatureRepository
from pdf_smartforms.ui.pdf_analysis_dialog import PdfAnalysisDialog

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
