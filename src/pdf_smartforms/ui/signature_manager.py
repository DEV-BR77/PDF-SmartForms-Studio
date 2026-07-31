"""Signature library UI."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pdf_smartforms.domain.signatures import SignatureAsset, SignatureOwner
from pdf_smartforms.signatures.image_processing import SignatureImageError
from pdf_smartforms.signatures.repository import SignatureRepository

_OWNER_LABELS = {
    SignatureOwner.GUARDIAN_1: "Erziehungsberechtigte Person 1",
    SignatureOwner.GUARDIAN_2: "Erziehungsberechtigte Person 2",
}


class SignatureManagerDialog(QDialog):
    """Import and delete local signature images."""

    def __init__(self, repository: SignatureRepository, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.repository = repository
        self.assets: list[SignatureAsset] = []
        self.setWindowTitle("Unterschriften verwalten")
        self.resize(760, 500)
        layout = QVBoxLayout(self)
        heading = QLabel("Unterschriftenbilder")
        heading.setObjectName("title")
        layout.addWidget(heading)
        warning = QLabel(
            "Unterschriftenbilder sind besonders schützenswert. Sie sind keine "
            "qualifizierten elektronischen oder zertifikatbasierten Signaturen."
        )
        warning.setWordWrap(True)
        layout.addWidget(warning)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Name", "Person", "Größe", "Datei-ID", "Vorschau"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        options = QHBoxLayout()
        self.remove_white = QCheckBox("Weißen Hintergrund transparent machen")
        self.remove_white.setChecked(True)
        self.improve_contrast = QCheckBox("Kontrast verbessern")
        self.improve_contrast.setChecked(True)
        options.addWidget(self.remove_white)
        options.addWidget(self.improve_contrast)
        layout.addLayout(options)
        actions = QHBoxLayout()
        import_button = QPushButton("PNG/JPG importieren")
        import_button.setObjectName("primary")
        import_button.clicked.connect(self._import_image)
        delete_button = QPushButton("Unterschrift löschen")
        delete_button.clicked.connect(self._delete_asset)
        actions.addWidget(import_button)
        actions.addWidget(delete_button)
        actions.addStretch()
        layout.addLayout(actions)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._reload()

    def _reload(self) -> None:
        self.assets = self.repository.list()
        self.table.setRowCount(len(self.assets))
        for row, asset in enumerate(self.assets):
            values = (
                asset.name,
                _OWNER_LABELS[asset.owner],
                f"{asset.width} × {asset.height} px",
                asset.id[:8],
            )
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
            preview = QPushButton("Anzeigen")
            preview.setFixedSize(78, 28)
            preview.setAccessibleName(f"Vorschau der Unterschrift {asset.name}")
            preview.clicked.connect(
                lambda _checked=False, selected=asset: self._preview_asset(selected)
            )
            self.table.setCellWidget(row, 4, preview)
        self.table.resizeColumnsToContents()

    def _preview_asset(self, asset: SignatureAsset) -> None:
        pixmap = QPixmap(str(self.repository.image_path(asset)))
        if pixmap.isNull():
            QMessageBox.warning(
                self, "Vorschau nicht möglich", "Das Unterschriftenbild ist nicht lesbar."
            )
            return
        preview = QDialog(self)
        preview.setWindowTitle(f"Vorschau · {asset.name}")
        preview.resize(560, 260)
        layout = QVBoxLayout(preview)
        image = QLabel()
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image.setPixmap(
            pixmap.scaled(
                500,
                170,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        layout.addWidget(image)
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(preview.reject)
        layout.addWidget(close)
        preview.exec()

    def _selected_asset(self) -> SignatureAsset | None:
        row = self.table.currentRow()
        return self.assets[row] if 0 <= row < len(self.assets) else None

    def _import_image(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "Unterschrift auswählen", "", "Bilder (*.png *.jpg *.jpeg)"
        )
        if not filename:
            return
        owner_text, accepted = QInputDialog.getItem(
            self,
            "Person auswählen",
            "Diese Unterschrift gehört zu:",
            list(_OWNER_LABELS.values()),
            0,
            False,
        )
        if not accepted:
            return
        owner = next(key for key, label in _OWNER_LABELS.items() if label == owner_text)
        name, accepted = QInputDialog.getText(
            self,
            "Name der Unterschrift",
            "Anzeigename:",
            text=Path(filename).stem,
        )
        if not accepted:
            return
        try:
            self.repository.import_image(
                Path(filename),
                name,
                owner,
                remove_white_background=self.remove_white.isChecked(),
                improve_contrast=self.improve_contrast.isChecked(),
            )
        except (OSError, SignatureImageError, ValueError) as error:
            QMessageBox.critical(self, "Import fehlgeschlagen", str(error))
            return
        self._reload()

    def _delete_asset(self) -> None:
        asset = self._selected_asset()
        if asset is None:
            QMessageBox.information(
                self, "Unterschrift auswählen", "Bitte zuerst eine Unterschrift auswählen."
            )
            return
        answer = QMessageBox.warning(
            self,
            "Unterschrift wirklich löschen?",
            f"„{asset.name}“ wird dauerhaft aus der lokalen Bibliothek gelöscht.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.repository.delete(asset.id)
            self._reload()
