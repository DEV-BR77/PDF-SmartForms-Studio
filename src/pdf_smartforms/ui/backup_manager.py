"""Guided local backup and restore interface."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pdf_smartforms.backup.archive import (
    BACKUP_AREAS,
    UnsafeBackup,
    create_backup,
    inspect_backup,
    restore_backup,
)
from pdf_smartforms.build_info import __version__
from pdf_smartforms.infrastructure.paths import AppPaths

AREA_LABELS = {
    "profiles": "Profile",
    "templates": "Templates",
    "field_dictionary": "Feldlexikon",
    "distribution_lists": "Verteilerlisten",
    "settings": "Einstellungen",
    "signatures": "Unterschriften (besonders sensibel)",
}


class BackupManagerDialog(QDialog):
    """Create and restore validated backups with explicit conflict handling."""

    def __init__(self, paths: AppPaths, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.paths = paths
        self.setWindowTitle("Datensicherung und Wiederherstellung")
        self.setMinimumWidth(560)
        layout = QVBoxLayout(self)
        heading = QLabel("Lokale Datensicherung")
        heading.setObjectName("title")
        layout.addWidget(heading)
        note = QLabel(
            "Standardmäßig werden keine Unterschriften oder erzeugten Dokumente gesichert. "
            "Die Sicherung ist lokal, offen strukturiert und durch Prüfsummen geschützt."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        self.area_checks: dict[str, QCheckBox] = {}
        for area in BACKUP_AREAS:
            checkbox = QCheckBox(AREA_LABELS[area])
            checkbox.setChecked(True)
            self.area_checks[area] = checkbox
            layout.addWidget(checkbox)
        signatures = QCheckBox(AREA_LABELS["signatures"])
        signatures.setAccessibleDescription(
            "Unterschriften sind besonders schützenswert und standardmäßig ausgeschlossen."
        )
        self.area_checks["signatures"] = signatures
        layout.addWidget(signatures)
        create_button = QPushButton("Sicherung erstellen")
        create_button.setObjectName("primary")
        create_button.clicked.connect(self._create)
        restore_button = QPushButton("Sicherung prüfen und wiederherstellen")
        restore_button.clicked.connect(self._restore)
        layout.addWidget(create_button)
        layout.addWidget(restore_button)

    def _selected_areas(self) -> tuple[str, ...]:
        return tuple(area for area, checkbox in self.area_checks.items() if checkbox.isChecked())

    def _create(self) -> None:
        areas = self._selected_areas()
        if not areas:
            QMessageBox.warning(self, "Keine Daten gewählt", "Wähle mindestens einen Bereich aus.")
            return
        default = self.paths.backups / f"pdf-smartforms-{datetime.now():%Y%m%d-%H%M}.psfsbackup"
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Datensicherung speichern",
            str(default),
            "PDF SmartForms Sicherung (*.psfsbackup)",
        )
        if not filename:
            return
        if "signatures" in areas:
            answer = QMessageBox.warning(
                self,
                "Sensible Daten",
                "Diese Sicherung enthält Bildunterschriften und ist noch nicht verschlüsselt. "
                "Bewahre sie ausschließlich an einem geschützten Ort auf.",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if answer != QMessageBox.StandardButton.Ok:
                return
        try:
            target = create_backup(Path(filename), self.paths, __version__, areas)
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "Sicherung fehlgeschlagen", str(error))
            return
        QMessageBox.information(self, "Sicherung erstellt", f"Gespeichert unter:\n{target}")

    def _restore(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Datensicherung auswählen",
            str(self.paths.backups),
            "PDF SmartForms Sicherung (*.psfsbackup *.zip)",
        )
        if not filename:
            return
        path = Path(filename)
        try:
            info = inspect_backup(path, self.paths)
        except (OSError, UnsafeBackup, ValueError) as error:
            QMessageBox.critical(self, "Wiederherstellung blockiert", str(error))
            return
        summary = (
            f"Erstellt: {info.created_at}\n"
            f"Programmversion: {info.application_version}\n"
            f"Bereiche: {', '.join(info.areas)}\n"
            f"Dateien: {len(info.files)}\n"
            f"Konflikte: {len(info.conflicts)}\n\n"
            "Vorhandene Dateien werden standardmäßig nicht überschrieben."
        )
        answer = QMessageBox.question(
            self,
            "Wiederherstellungsvorschau",
            summary,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            recovery_point = (
                self.paths.backups / f"before-restore-{datetime.now():%Y%m%d-%H%M%S}.psfsbackup"
            )
            create_backup(recovery_point, self.paths, __version__, BACKUP_AREAS)
            restore_backup(path, self.paths, replace=False)
        except (OSError, UnsafeBackup, ValueError) as error:
            QMessageBox.critical(self, "Wiederherstellung fehlgeschlagen", str(error))
            return
        QMessageBox.information(
            self,
            "Wiederherstellung abgeschlossen",
            "Neue Dateien wurden wiederhergestellt. Bestehende Dateien blieben unverändert.\n\n"
            f"Sicherungspunkt vor der Wiederherstellung:\n{recovery_point}",
        )
