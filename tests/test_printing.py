from PyQt6.QtCore import QRectF

from pdf_smartforms.printing.service import _fit_page


def test_printed_page_is_centered_and_keeps_aspect_ratio() -> None:
    target = _fit_page(QRectF(0, 0, 1000, 700), 600, 900)

    assert target.height() == 700
    assert round(target.width(), 3) == round(600 * (700 / 900), 3)
    assert target.center() == QRectF(0, 0, 1000, 700).center()
