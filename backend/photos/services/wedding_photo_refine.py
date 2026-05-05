"""
Refine a merged bride + guest photo using OpenAI image editing.

Uses GPT Image models with high input fidelity when available to preserve faces while
harmonizing lighting, color, and realism. Falls back to DALL-E 2 (square) if configured.
"""

from __future__ import annotations

import base64
import logging
import os
import tempfile
import uuid
from io import BytesIO
from pathlib import Path
from typing import Literal

from django.conf import settings
from PIL import Image

from openai import OpenAI

from .image_resize import resize_to_square_with_padding

logger = logging.getLogger(__name__)

__all__ = ["refine_merged_wedding_photo", "REFINE_PROMPT"]

# Prompt tuned for image *editing*: preserve identity, improve global realism.
REFINE_PROMPT = """
Transform this into a single, photorealistic professional wedding photograph.
Unify lighting, shadows, color temperature, and exposure across the entire frame so the
bride and the other person clearly belong in the same scene and moment.
Add subtle, physically plausible contact shadows and ambient light that match the venue.
Refine edge blending and skin tone consistency without altering anyone's identity.
Keep every face exactly as in the source: same facial features, expressions, age, and
skin texture — do not beautify, slim, or replace faces.
High detail, natural skin, realistic fabric and background, editorial wedding quality.
""".strip()


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Set it in your environment or Django settings."
        )
    return OpenAI(api_key=api_key)


def _refine_model() -> str:
    return getattr(
        settings,
        "OPENAI_REFINE_MODEL",
        os.getenv("OPENAI_REFINE_MODEL", "gpt-image-1.5"),
    )


def _refine_size_gpt() -> Literal["1024x1024", "1024x1536", "1536x1024", "auto"]:
    raw = getattr(
        settings,
        "OPENAI_REFINE_SIZE",
        os.getenv("OPENAI_REFINE_SIZE", "1536x1024"),
    )
    allowed = {"1024x1024", "1024x1536", "1536x1024", "auto"}
    if raw not in allowed:
        logger.warning("Invalid OPENAI_REFINE_SIZE %r; using 1536x1024", raw)
        return "1536x1024"
    return raw  # type: ignore[return-value]


def _is_gpt_image_model(model: str) -> bool:
    m = model.lower()
    return m.startswith("gpt-image") or m.startswith("chatgpt-image")


def _prepare_input_png(path: Path, max_long_edge: int = 4096) -> bytes:
    """
    Load image and emit PNG bytes suitable for the edit API (≤50 MB for GPT models).
    Downscales if the longest edge exceeds ``max_long_edge``.
    """
    with Image.open(path) as img:
        img.load()
        im = img.convert("RGBA") if img.mode in ("RGBA", "LA", "P") else img.convert("RGB")
        w, h = im.size
        m = max(w, h)
        if m > max_long_edge:
            scale = max_long_edge / m
            nw = max(1, int(round(w * scale)))
            nh = max(1, int(round(h * scale)))
            im = im.resize((nw, nh), Image.Resampling.LANCZOS)
        buf = BytesIO()
        im.save(buf, format="PNG", optimize=True)
        data = buf.getvalue()
    if len(data) > 50 * 1024 * 1024:
        raise ValueError(
            "Prepared PNG exceeds 50 MB after resize; use a smaller source image."
        )
    return data


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


def refine_merged_wedding_photo(
    merged_image_path: str | Path,
    *,
    prompt: str | None = None,
    model: str | None = None,
) -> str:
    """
    Improve a merged bride + guest image for photorealistic wedding-photo quality.

    Harmonizes lighting, shadows, and color; preserves faces via GPT Image
    ``input_fidelity=high`` when using OpenAI directly (GPT Image models).

    Parameters
    ----------
    merged_image_path:
        Path to the composite image (PNG/JPEG/WebP, etc.).
    prompt:
        Override the default refinement prompt.
    model:
        Override ``OPENAI_REFINE_MODEL`` / settings (OpenAI path only).

    Returns
    -------
    str
        Relative path under ``MEDIA_ROOT`` (e.g. ``generated/abc.png``).

    Raises
    ------
    RuntimeError
        On missing API key or API failures.
    ValueError
        On missing file or invalid input.
    """
    path = Path(merged_image_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Merged image not found: {path}")

    text = (prompt or REFINE_PROMPT).strip()

    use_model = (model or _refine_model()).strip()
    client = _client()

    if _is_gpt_image_model(use_model):
        png_bytes = _prepare_input_png(path)
        size = _refine_size_gpt()
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        try:
            tmp.write(png_bytes)
            tmp.close()
            fidelity_kw = (
                {"input_fidelity": "high"}
                if "mini" not in use_model.lower()
                else {}
            )
            with open(tmp.name, "rb") as f:
                result = client.images.edit(
                    model=use_model,
                    prompt=text,
                    image=("merged.png", f, "image/png"),
                    size=size,
                    quality="high",
                    output_format="png",
                    **fidelity_kw,
                )
        finally:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass

        out_bytes = _response_to_png_bytes(result)
    else:
        # DALL-E 2: single square PNG, max 4 MB
        square = resize_to_square_with_padding(path, side=1024, fill=(255, 255, 255))
        buf = BytesIO()
        square.save(buf, format="PNG", optimize=True)
        png_bytes = buf.getvalue()
        if len(png_bytes) > 4 * 1024 * 1024:
            raise ValueError("Square PNG exceeds 4 MB limit for DALL-E 2.")

        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        try:
            tmp.write(png_bytes)
            tmp.close()
            with open(tmp.name, "rb") as f:
                result = client.images.edit(
                    model="dall-e-2",
                    prompt=text[:1000],
                    image=("merged.png", f, "image/png"),
                    size="1024x1024",
                    n=1,
                    response_format="b64_json",
                )
        finally:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass

        out_bytes = _response_to_png_bytes(result)

    media_root = Path(getattr(settings, "MEDIA_ROOT", "media"))
    generated_dir = media_root / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.png"
    rel = f"generated/{filename}"
    abs_path = generated_dir / filename
    abs_path.write_bytes(out_bytes)
    logger.info("Saved refined wedding photo to %s", abs_path)
    return rel.replace("\\", "/")
