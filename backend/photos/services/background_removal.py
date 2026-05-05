"""
Remove image backgrounds with rembg; output transparent PNG bytes and save locally.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import BinaryIO, Union

# rembg downloads u2net.onnx (~176MB) via pooch; default HTTP timeout is 30s and causes
# HTTPSConnectionPool(... release-assets.githubusercontent.com): Read timed out on slow links.
import pooch.downloaders as _pooch_dl

_pooch_dl.DEFAULT_TIMEOUT = int(os.getenv("REMBG_DOWNLOAD_TIMEOUT", "1800"))

from rembg import remove
from rembg.session_factory import new_session

logger = logging.getLogger(__name__)

PathLike = Union[str, Path]

__all__ = [
    "remove_background_to_png",
    "remove_background_from_bytes",
    "remove_background_to_png_stream",
]


def remove_background_to_png(
    input_path: PathLike,
    output_path: PathLike | None = None,
    *,
    model_name: str = "u2net",
    alpha_matting: bool = False,
) -> bytes:
    """
    Remove the background from an image and return PNG bytes (RGBA, transparent).

    Optionally writes the same bytes to ``output_path``. If ``output_path`` is omitted,
    defaults to ``<input_stem>_nobg.png`` beside the input file.

    Parameters
    ----------
    input_path:
        Path to the source image (formats supported by Pillow / rembg).
    output_path:
        Destination path for the PNG. Parent directories are created if needed.
    model_name:
        rembg model id (e.g. ``u2net``, ``u2net_human_seg``, ``isnet-general-use``).
    alpha_matting:
        Enable alpha matting for smoother edges (slightly slower).

    Returns
    -------
    bytes
        Encoded transparent PNG.

    Raises
    ------
    FileNotFoundError
        If ``input_path`` is not a file.
    ValueError
        If input cannot be read or processing returns empty output.
    """
    src = Path(input_path).expanduser().resolve()
    if not src.is_file():
        raise FileNotFoundError(f"Input image not found: {src}")

    dst: Path | None
    if output_path is not None:
        dst = Path(output_path).expanduser().resolve()
        dst.parent.mkdir(parents=True, exist_ok=True)
    else:
        dst = src.with_name(f"{src.stem}_nobg.png")

    session = new_session(model_name)

    try:
        input_bytes = src.read_bytes()
    except OSError as e:
        raise ValueError(f"Cannot read image file: {src}") from e

    if not input_bytes:
        raise ValueError(f"Empty file: {src}")

    try:
        png_bytes = remove(
            input_bytes,
            session=session,
            alpha_matting=alpha_matting,
        )
    except Exception as e:
        logger.exception("rembg.remove failed for %s", src)
        raise ValueError(f"Background removal failed: {e}") from e

    if not png_bytes:
        raise ValueError("Background removal produced empty output")

    try:
        dst.write_bytes(png_bytes)
    except OSError as e:
        raise ValueError(f"Cannot write output PNG: {dst}") from e

    logger.debug("Saved transparent PNG to %s (%s bytes)", dst, len(png_bytes))
    return png_bytes


def remove_background_from_bytes(
    image_bytes: bytes,
    *,
    model_name: str = "u2net",
    alpha_matting: bool = False,
) -> bytes:
    """
    Same as :func:`remove_background_to_png` but accepts raw image bytes (no file read).
    Does not save to disk; use when data is already in memory.
    """
    if not image_bytes:
        raise ValueError("image_bytes is empty")

    session = new_session(model_name)
    png_bytes = remove(
        image_bytes,
        session=session,
        alpha_matting=alpha_matting,
    )
    if not png_bytes:
        raise ValueError("Background removal produced empty output")
    return png_bytes


def remove_background_to_png_stream(
    input_file: BinaryIO,
    output_path: PathLike,
    *,
    model_name: str = "u2net",
    alpha_matting: bool = False,
) -> bytes:
    """
    Read image from a binary stream, remove background, save PNG to ``output_path``, return bytes.
    """
    input_bytes = input_file.read()
    if not input_bytes:
        raise ValueError("Input stream is empty")

    dst = Path(output_path).expanduser().resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)

    session = new_session(model_name)
    png_bytes = remove(
        input_bytes,
        session=session,
        alpha_matting=alpha_matting,
    )
    if not png_bytes:
        raise ValueError("Background removal produced empty output")

    dst.write_bytes(png_bytes)
    return png_bytes
