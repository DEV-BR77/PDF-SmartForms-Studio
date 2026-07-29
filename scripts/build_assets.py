"""Render repository-owned vector artwork into Windows and documentation assets."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QByteArray, QSize, Qt
from PyQt6.QtGui import QGuiApplication, QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "assets" / "app-icon.svg"
PNG = ROOT / "assets" / "app-icon.png"
ICO = ROOT / "assets" / "app-icon.ico"


def render(size: int) -> QImage:
    image = QImage(QSize(size, size), QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer = QSvgRenderer(QByteArray(SVG.read_bytes()))
    renderer.render(painter)
    painter.end()
    return image


def main() -> None:
    _ = QGuiApplication.instance() or QGuiApplication([])
    PNG.parent.mkdir(parents=True, exist_ok=True)
    if not render(512).save(str(PNG), "PNG"):
        raise RuntimeError("PNG-Icon konnte nicht gespeichert werden.")
    if not render(256).save(str(ICO), "ICO"):
        raise RuntimeError("Windows-Icon konnte nicht gespeichert werden.")
    print(f"Assets erstellt: {PNG.name}, {ICO.name}")


if __name__ == "__main__":
    main()
