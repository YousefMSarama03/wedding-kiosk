"""
Resize images to a square canvas while preserving aspect ratio (letterbox padding).
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple, Union

from PIL import Image

PathLike = Union[str, Path]

__all__ = ["resize_to_square_with_padding"]


def _to_rgb_on_background(img: Image.Image, rgb: Tuple[int, int, int]) -> Image.Image:
    """Flatten alpha (if any) onto a solid RGB background."""
    if img.mode in ("RGBA", "LA"):
        if img.mode == "LA":
            img = img.convert("RGBA")
        base = Image.new("RGB", img.size, rgb)
        base.paste(img, mask=img.split()[3])
        return base
    if img.mode == "P":
        img = img.convert("RGBA")
        return _to_rgb_on_background(img, rgb)
    return img.convert("RGB")


def _to_rgba(img: Image.Image) -> Image.Image:
    if img.mode == "RGBA":
        return img
    if img.mode == "P":
        img = img.convert("RGBA")
        return img
    return img.convert("RGBA")


def resize_to_square_with_padding(
    image: PathLike | Image.Image,
    side: int = 1024,
    *,
    fill: Tuple[int, int, int] | Tuple[int, int, int, int] = (255, 255, 255),
    resample: int = Image.Resampling.LANCZOS,
) -> Image.Image:
    """
    Scale an image so it fits inside ``side``×``side`` while keeping aspect ratio,
    then center it on a square canvas padded with ``fill``.

    Parameters
    ----------
    image:
        File path or a Pillow image. Paths are opened read-only; the source file is not modified.
    side:
        Output width and height in pixels (default 1024).
    fill:
        Padding color: ``(R, G, B)`` for an ``RGB`` result, or ``(R, G, B, A)`` for ``RGBA``.
    resample:
        Resampling filter (default ``LANCZOS``).

    Returns
    -------
    PIL.Image.Image
        A new ``side``×``side`` image (``RGB`` or ``RGBA``).

    Raises
    ------
    ValueError
        If ``side`` is less than 1 or ``fill`` is not length 3 or 4.
    FileNotFoundError
        If ``image`` is a path that does not exist.
    """
    if side < 1:
        raise ValueError(f"side must be >= 1, got {side}")
    if len(fill) not in (3, 4):
        raise ValueError("fill must be an (R, G, B) or (R, G, B, A) tuple")

    if isinstance(image, (str, Path)):
        path = Path(image).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Image not found: {path}")
        src = Image.open(path)
        src.load()
    else:
        src = image.copy()

    w, h = src.size
    if w < 1 or h < 1:
        raise ValueError(f"Invalid source size: {w}x{h}")

    scale = min(side / w, side / h)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    resized = src.resize((new_w, new_h), resample)

    x0 = (side - new_w) // 2
    y0 = (side - new_h) // 2

    if len(fill) == 4:
        canvas = Image.new("RGBA", (side, side), fill)
        layer = _to_rgba(resized)
        canvas.paste(layer, (x0, y0), layer)
    else:
        canvas = Image.new("RGB", (side, side), fill[:3])
        layer = _to_rgb_on_background(resized, fill[:3])
        canvas.paste(layer, (x0, y0))

    return canvas
