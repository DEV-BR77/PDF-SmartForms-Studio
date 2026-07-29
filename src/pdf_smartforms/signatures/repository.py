"""Local signature image repository."""

from __future__ import annotations

import json
import os
from pathlib import Path

from pdf_smartforms.domain.signatures import SignatureAsset, SignatureOwner
from pdf_smartforms.signatures.image_processing import process_signature_image

AssetList = list[SignatureAsset]


class SignatureRepository:
    """Store normalized signature PNGs under opaque filenames."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.images = directory / "images"
        self.manifest = directory / "signatures.json"
        self.images.mkdir(parents=True, exist_ok=True)

    def list(self) -> AssetList:
        assets = self._load_assets()
        return sorted(assets, key=lambda item: (item.owner.value, item.name.casefold()))

    def import_image(
        self,
        source: Path,
        name: str,
        owner: SignatureOwner,
        *,
        remove_white_background: bool = True,
        improve_contrast: bool = True,
    ) -> SignatureAsset:
        provisional = SignatureAsset.create(name.strip() or source.stem, owner, 1, 1)
        target = self.images / provisional.filename
        width, height = process_signature_image(
            source,
            target,
            remove_white_background=remove_white_background,
            improve_contrast=improve_contrast,
        )
        asset = SignatureAsset(
            provisional.id,
            provisional.name,
            provisional.owner,
            provisional.filename,
            width,
            height,
        )
        assets = self._load_assets()
        assets.append(asset)
        self._save_assets(assets)
        return asset

    def image_path(self, asset: SignatureAsset) -> Path:
        return self.images / asset.filename

    def delete(self, asset_id: str) -> bool:
        assets = self._load_assets()
        retained = [asset for asset in assets if asset.id != asset_id]
        if len(retained) == len(assets):
            return False
        asset = next(item for item in assets if item.id == asset_id)
        image = self.image_path(asset)
        if image.exists():
            image.unlink()
        self._save_assets(retained)
        return True

    def _load_assets(self) -> AssetList:
        if not self.manifest.exists():
            return []
        payload = json.loads(self.manifest.read_text(encoding="utf-8"))
        return [SignatureAsset.from_dict(item) for item in payload.get("assets", [])]

    def _save_assets(self, assets: AssetList) -> None:
        temporary = self.manifest.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "assets": [asset.to_dict() for asset in assets],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        os.replace(temporary, self.manifest)
