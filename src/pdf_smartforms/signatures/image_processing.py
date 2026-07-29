"""Safe signature image normalization."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageEnhance, UnidentifiedImageError

MAX_IMAGE_SIZE = 15 * 1024 * 1024
MAX_PIXELS = 25_000_000
ALLOWED_FORMATS = {"PNG", "JPEG"}


class SignatureImageError(ValueError):
    """Image is invalid or exceeds safe limits."""


def process_signature_image(
    source: Path,
    target: Path,
    *,
    remove_white_background: bool = True,
    improve_contrast: bool = True,
) -> tuple[int, int]:
    """Validate, normalize, crop and save an RGBA PNG."""
    if not source.exists() or source.stat().st_size > MAX_IMAGE_SIZE:
        raise SignatureImageError("Bild fehlt oder überschreitet das Größenlimit.")
    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    try:
        with Image.open(source) as probe:
            if probe.format not in ALLOWED_FORMATS:
                raise SignatureImageError("Nur echte PNG- und JPEG-Bilder werden unterstützt.")
            probe.verify()
        with Image.open(source) as opened:
            image = opened.convert("RGBA")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise SignatureImageError(
            "Bild ist beschädigt oder kann nicht sicher gelesen werden."
        ) from error
    if improve_contrast:
        rgb = Image.new("RGB", image.size, "white")
        rgb.paste(image, mask=image.getchannel("A"))
        rgb = ImageEnhance.Contrast(rgb).enhance(1.45)
        image = rgb.convert("RGBA")
    if remove_white_background:
        pixels: Any = image.load()
        for y_position in range(image.height):
            for x_position in range(image.width):
                red, green, blue, alpha = pixels[x_position, y_position]
                if min(red, green, blue) >= 245:
                    pixels[x_position, y_position] = (red, green, blue, 0)
    alpha = image.getchannel("A")
    bounding_box = alpha.getbbox()
    if bounding_box is None:
        raise SignatureImageError("Nach der Bereinigung ist keine Unterschrift sichtbar.")
    image = image.crop(bounding_box)
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format="PNG", optimize=True)
    return image.size
