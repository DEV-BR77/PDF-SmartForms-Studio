"""Create repeatable screenshots with synthetic local data."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from PyQt6.QtWidgets import QApplication, QWidget

from pdf_smartforms.domain.safety import SafetyReview
from pdf_smartforms.infrastructure.paths import create_app_paths
from pdf_smartforms.ui.backup_manager import BackupManagerDialog
from pdf_smartforms.ui.main_window import MainWindow
from pdf_smartforms.ui.safety_review_dialog import SafetyReviewDialog
from pdf_smartforms.ui.theme import application_stylesheet

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "docs" / "screenshots"


def capture(widget: QWidget, name: str) -> None:
    widget.show()
    QApplication.processEvents()
    image = widget.grab()
    target = TARGET / name
    if not image.save(str(target), "PNG"):
        raise RuntimeError(f"Screenshot konnte nicht gespeichert werden: {target}")
    widget.close()


def main() -> None:
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(application_stylesheet())
    TARGET.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory() as directory:
        paths = create_app_paths(Path(directory))
        main_window = MainWindow(paths)
        main_window.resize(1100, 720)
        capture(main_window, "01-startseite.png")
        backup = BackupManagerDialog(paths)
        backup.resize(680, 620)
        capture(backup, "02-datensicherung.png")
        safety = SafetyReviewDialog(
            SafetyReview(
                action="E-Mail-Entwurf",
                document_name="Anmeldung_Sportverein.pdf",
                mapped_fields=8,
                unresolved_fields=1,
                signatures=1,
                recipients=("verein@example.org",),
                subject="Anmeldung Sportverein",
                attachments=("Anmeldung_Sportverein.pdf",),
            )
        )
        safety.resize(680, 520)
        capture(safety, "03-sicherheitsvorschau.png")
    print(f"Screenshots erstellt: {TARGET}")


if __name__ == "__main__":
    main()
