"""
Generic helper for OpenAI Images API (``images.edit``).

API key: ``OPENAI_API_KEY`` environment variable, or Django ``settings.OPENAI_API_KEY``
when running inside a Django app (``python-dotenv`` loads ``.env`` in ``settings``).
"""

from __future__ import annotations

import base64
import logging
import os
import tempfile
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Union

from openai import OpenAI

logger = logging.getLogger(__name__)

PathLike = Union[str, Path]
ImageInput = Union[PathLike, bytes, BinaryIO]

__all__ = ["edit_image_openai", "get_openai_api_key"]


def get_openai_api_key() -> str:
    """
    Resolve the OpenAI API key (best practice: never hardcode).

    Order: ``os.environ["OPENAI_API_KEY"]``, then Django ``settings.OPENAI_API_KEY``.
    """
    key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if key:
        return key
    try:
        from django.conf import settings

        key = (getattr(settings, "OPENAI_API_KEY", None) or "").strip()
    except Exception:
        key = ""
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Export it in the environment or set it in Django settings."
        )
    return key


def _client() -> OpenAI:
    return OpenAI(api_key=get_openai_api_key())


def _default_edit_model() -> str:
    try:
        from django.conf import settings

        s = (getattr(settings, "OPENAI_IMAGE_EDIT_MODEL", None) or "").strip()
        if s:
            return s
    except Exception:
        pass
    return (
        os.getenv("OPENAI_IMAGE_EDIT_MODEL")
        or os.getenv("OPENAI_IMAGE_MODEL")
        or "gpt-image-1.5"
    ).strip()


def _is_gpt_image_model(model: str) -> bool:
    m = model.lower()
    return m.startswith("gpt-image") or m.startswith("chatgpt-image")


def _load_pil_image(image: ImageInput):
    from PIL import Image

    if isinstance(image, (str, Path)):
        p = Path(image).expanduser().resolve()
        if not p.is_file():
            raise FileNotFoundError(f"Image not found: {p}")
        im = Image.open(p)
    elif isinstance(image, bytes):
        im = Image.open(BytesIO(image))
    else:
        im = Image.open(image)
    im.load()
    return im.convert("RGBA") if im.mode in ("RGBA", "LA", "P") else im.convert("RGB")


def _image_to_temp_png_file(image: ImageInput, *, square_side: int | None = None) -> Path:
    """
    Materialize input as a PNG on disk for multipart upload with a correct MIME type.

    OpenAI ``images.edit`` expects a file-like object with ``image/png`` (or jpeg/webp
    for GPT image models); raw bytes alone can be rejected.

    For DALL-E 2, pass ``square_side=1024`` — the API requires a square PNG under 4 MB.
    """
    rgba = _load_pil_image(image)
    if square_side is not None:
        from .image_resize import resize_to_square_with_padding

        rgba = resize_to_square_with_padding(rgba, side=square_side, fill=(255, 255, 255))

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    try:
        rgba.save(tmp.name, format="PNG", optimize=True)
        if os.path.getsize(tmp.name) > 4 * 1024 * 1024 and square_side is not None:
            raise ValueError(
                "Prepared PNG exceeds 4 MB (DALL-E 2 limit). Use a smaller source image or a GPT Image model."
            )
        tmp.close()
        return Path(tmp.name)
    except Exception:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
        raise


def _response_to_png_bytes(result) -> bytes:
    if not result.data:
        raise RuntimeError("OpenAI returned no image data.")
    item = result.data[0]
    if item.b64_json:
        return base64.b64decode(item.b64_json)
    if item.url:
        import requests

        r = requests.get(item.url, timeout=120)
        r.raise_for_status()
        return r.content
    raise RuntimeError("OpenAI image response has neither b64_json nor url.")


def edit_image_openai(
    image: ImageInput,
    prompt: str,
    *,
    model: str | None = None,
    size: str | None = None,
    quality: str = "high",
    input_fidelity: str | None = "high",
    timeout: float | None = 120.0,
) -> bytes:
    """
    Send an image to OpenAI ``images.edit`` and return the edited image as PNG/JPEG bytes.

    Parameters
    ----------
    image:
        Path to an image file, raw bytes, or a binary stream readable by Pillow.
    prompt:
        Edit instruction (max length depends on model; DALL-E 2 allows up to 1000 characters).
    model:
        Override model (default: ``OPENAI_IMAGE_EDIT_MODEL``, then ``OPENAI_IMAGE_MODEL``, then
        ``gpt-image-1.5``). Use ``dall-e-2`` for widest compatibility (square input/output).
    size:
        Output size. GPT Image models: ``1024x1024``, ``1024x1536``, ``1536x1024``, ``auto``.
        DALL-E 2: ``256x256``, ``512x512``, ``1024x1024``.
    quality:
        For GPT Image models: ``low``, ``medium``, ``high``, or ``auto``.
    input_fidelity:
        For GPT Image models (not ``gpt-image-1-mini``): ``high`` or ``low`` to stay closer to
        the source image. Set to ``None`` to omit (API default).
    timeout:
        HTTP timeout in seconds for the request (passed to the OpenAI client call).

    Returns
    -------
    bytes
        Decoded image bytes from the API response.

    Environment
    -----------
    OPENAI_API_KEY
        Required (unless set in Django settings).
    OPENAI_IMAGE_EDIT_MODEL
        Optional default model for this helper.
    """
    use_model = (model or _default_edit_model()).strip()
    text = prompt.strip()
    if not text:
        raise ValueError("prompt must be non-empty.")

    if _is_gpt_image_model(use_model):
        tmp_path = _image_to_temp_png_file(image, square_side=None)
    elif use_model.lower() == "dall-e-2":
        tmp_path = _image_to_temp_png_file(image, square_side=1024)
    else:
        raise ValueError(
            f"Unsupported image edit model: {use_model!r}. "
            "Use a GPT Image model (e.g. gpt-image-1.5) or dall-e-2."
        )

    try:
        client = _client()

        with open(tmp_path, "rb") as f:
            file_tuple = ("image.png", f, "image/png")

            if _is_gpt_image_model(use_model):
                sz = size or os.getenv("OPENAI_REFINE_SIZE") or "1536x1024"
                kwargs = {
                    "model": use_model,
                    "prompt": text,
                    "image": file_tuple,
                    "size": sz,
                    "quality": quality,
                    "output_format": "png",
                }
                if input_fidelity and "mini" not in use_model.lower():
                    kwargs["input_fidelity"] = input_fidelity
                if timeout is not None:
                    kwargs["timeout"] = timeout
                result = client.images.edit(**kwargs)
            else:
                kwargs = {
                    "model": "dall-e-2",
                    "prompt": text[:1000],
                    "image": file_tuple,
                    "size": size or "1024x1024",
                    "n": 1,
                    "response_format": "b64_json",
                }
                if timeout is not None:
                    kwargs["timeout"] = timeout
                result = client.images.edit(**kwargs)

        out = _response_to_png_bytes(result)
        logger.debug("OpenAI images.edit ok, model=%s, output_bytes=%s", use_model, len(out))
        return out
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
