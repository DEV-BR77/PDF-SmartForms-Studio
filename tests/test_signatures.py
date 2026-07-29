from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from pdf_smartforms.domain.signatures import SignatureAsset, SignatureOwner
from pdf_smartforms.signatures.image_processing import (
    SignatureImageError,
    process_signature_image,
)
from pdf_smartforms.signatures.repository import SignatureRepository


def create_signature(path: Path) -> None:
    image = Image.new("RGB", (500, 180), "white")
    draw = ImageDraw.Draw(image)
    draw.line((80, 100, 180, 60, 260, 110, 400, 65), fill="black", width=5)
    image.save(path)


def test_signature_processing_crops_and_removes_white_background(
    tmp_path: Path,
) -> None:
    source = tmp_path / "signature.jpg"
    target = tmp_path / "processed.png"
    create_signature(source)
    width, height = process_signature_image(source, target)
    assert width < 500
    assert height < 180
    with Image.open(target) as image:
        assert image.mode == "RGBA"
        assert image.getchannel("A").getextrema()[0] == 0


def test_signature_repository_imports_lists_and_deletes(tmp_path: Path) -> None:
    source = tmp_path / "signature.png"
    create_signature(source)
    repository = SignatureRepository(tmp_path / "library")
    asset = repository.import_image(source, "Person 1", SignatureOwner.GUARDIAN_1)
    assert repository.list() == [asset]
    assert repository.image_path(asset).exists()
    assert repository.delete(asset.id)
    assert repository.list() == []
    assert not repository.delete(asset.id)


def test_signature_metadata_round_trip() -> None:
    asset = SignatureAsset.create("Test", SignatureOwner.GUARDIAN_2, 200, 80)
    assert SignatureAsset.from_dict(asset.to_dict()) == asset


def test_corrupt_or_empty_image_is_rejected(tmp_path: Path) -> None:
    corrupt = tmp_path / "signature.png"
    corrupt.write_bytes(b"not an image")
    with pytest.raises(SignatureImageError):
        process_signature_image(corrupt, tmp_path / "out.png")

    empty = tmp_path / "empty.png"
    Image.new("RGB", (100, 50), "white").save(empty)
    with pytest.raises(SignatureImageError):
        process_signature_image(empty, tmp_path / "empty-out.png")
