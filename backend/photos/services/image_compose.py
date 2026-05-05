"""
Composite a transparent guest image onto a background (e.g. bride photo).
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from PIL import Image

PathLike = Union[str, Path]

__all__ = ["merge_guest_on_background"]


def _load_image(image: PathLike | Image.Image) -> Image.Image:
    if isinstance(image, (str, Path)):
        path = Path(image).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Image not found: {path}")
        im = Image.open(path)
        im.load()
        return im
    return image.copy()


def _resize_contain(
    img: Image.Image,
    max_w: int,
    max_h: int,
    *,
    allow_upscale: bool,
    resample: int,
) -> Image.Image:
    """Scale image to fit inside max_w × max_h, preserving aspect ratio."""
    if max_w < 1 or max_h < 1:
        raise ValueError(f"max_guest_size must be positive, got ({max_w}, {max_h})")
    w, h = img.size
    if w < 1 or h < 1:
        raise ValueError(f"Invalid image size: {w}x{h}")
    scale = min(max_w / w, max_h / h)
    if not allow_upscale:
        scale = min(scale, 1.0)
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    if nw == w and nh == h:
        return img
    return img.resize((nw, nh), resample)


def _ensure_rgba_guest(img: Image.Image) -> Image.Image:
    """Ensure image has an alpha channel for correct masking."""
    if img.mode == "RGBA":
        return img
    if img.mode == "LA":
        return img.convert("RGBA")
    if img.mode == "P":
        t = img.info.get("transparency")
        if t is not None:
            return img.convert("RGBA")
        return img.convert("RGBA")
    # RGB or other: add opaque alpha
    return img.convert("RGBA")


def _paste_rgba_clipped(
    base_rgba: Image.Image,
    overlay_rgba: Image.Image,
    xy: tuple[int, int],
) -> Image.Image:
    """
    Paste overlay onto a copy of base at xy, clipping to base bounds.
    Preserves overlay alpha (third argument to paste).
    """
    x, y = xy
    bw, bh = base_rgba.size
    ow, oh = overlay_rgba.size

    ix0 = max(0, x)
    iy0 = max(0, y)
    ix1 = min(bw, x + ow)
    iy1 = min(bh, y + oh)
    if ix0 >= ix1 or iy0 >= iy1:
        return base_rgba.copy()

    sx0 = ix0 - x
    sy0 = iy0 - y
    sx1 = sx0 + (ix1 - ix0)
    sy1 = sy0 + (iy1 - iy0)

    cropped = overlay_rgba.crop((sx0, sy0, sx1, sy1))
    out = base_rgba.copy()
    out.paste(cropped, (ix0, iy0), cropped)
    return out


def merge_guest_on_background(
    background: PathLike | Image.Image,
    guest: PathLike | Image.Image,
    position: tuple[int, int],
    *,
    max_guest_size: tuple[int, int] | None = None,
    allow_upscale: bool = False,
    resample: int = Image.Resampling.LANCZOS,
) -> Image.Image:
    """
    Place a transparent PNG guest image onto a background (e.g. bride photo).

    The guest is scaled proportionally to fit within ``max_guest_size`` (if given),
    then composited at ``position`` = ``(x, y)`` (top-left of the guest on the background).
    Transparency in the guest is preserved.

    Parameters
    ----------
    background:
        Bride / scene image (path or ``PIL.Image``). Converted to ``RGBA`` for compositing.
    guest:
        Guest cutout, typically ``RGBA`` PNG (path or ``PIL.Image``).
    position:
        ``(x, y)`` pixel coordinates where the guest’s top-left corner is placed.
    max_guest_size:
        ``(max_width, max_height)`` bounding box; the guest is scaled down (or up if
        ``allow_upscale``) to fit while keeping aspect ratio. If ``None``, guest size is unchanged.
    allow_upscale:
        If ``False`` (default), never scale the guest larger than its original size when
        applying ``max_guest_size``.
    resample:
        Resampling filter for scaling (default ``LANCZOS``).

    Returns
    -------
    PIL.Image.Image
        A new ``RGBA`` image (same size as the background).

    Raises
    ------
    FileNotFoundError
        If a path does not exist.
    ValueError
        On invalid sizes or parameters.
    """
    bg = _load_image(background)
    guest_im = _load_image(guest)

    if bg.size[0] < 1 or bg.size[1] < 1:
        raise ValueError("Background has invalid dimensions")

    base = bg.convert("RGBA")
    overlay = _ensure_rgba_guest(guest_im)

    if max_guest_size is not None:
        mw, mh = max_guest_size
        overlay = _resize_contain(
            overlay,
            mw,
            mh,
            allow_upscale=allow_upscale,
            resample=resample,
        )

    return _paste_rgba_clipped(base, overlay, position)
