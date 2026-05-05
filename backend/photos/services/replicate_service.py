"""
Replicate InstantID (face-preserving) generation for wedding keepsake images.

Uses a pinned InstantID model on Replicate; identity comes from the guest image,
composition/pose hints from the bride reference image.
"""

from __future__ import annotations

import logging
import os
from io import BytesIO
from pathlib import Path
from typing import Any

import requests
import replicate
from django.conf import settings

logger = logging.getLogger(__name__)

__all__ = ["generate_wedding_image_with_replicate", "EVENT_PROMPTS", "EVENT_PROMPTS_SOLO"]

# Pinned version for stable API (zsxkib/instant-id). Override via REPLICATE_INSTANTID_MODEL.
DEFAULT_INSTANTID_MODEL = (
    "zsxkib/instant-id:2e4785a4d80dadf580077b2244c8d7c05d8e3faac04a04c02d8e099dd2876789"
)

EVENT_PROMPTS = {
    "wedding": """
A realistic wedding photo of a bride and a guest standing together.
The guest must have the exact same face and identity as the reference image.
The bride is wearing a luxurious white wedding dress.
Both are standing naturally side by side with correct proportions.
Perfect lighting, soft shadows, natural skin tones.
Professional wedding photography, shallow depth of field.
Highly realistic, 4k, no distortion, no extra fingers, no face change.
""".strip(),
    "palestinian_henna": """
A realistic Palestinian henna party portrait with celebratory atmosphere.
The guest must have the exact same face and identity as the reference image.
Include authentic Palestinian henna celebration styling, elegant traditional details,
warm festive lighting, and culturally respectful attire and decor.
Natural skin tones, true-to-life composition, and professional event photography quality.
Highly realistic, 4k, no distortion, no extra fingers, no face change.
""".strip(),
    "graduation": """
A realistic graduation celebration portrait.
The guest must have the exact same face and identity as the reference image.
Include graduation ceremony context with tasteful academic visual cues,
clean composition, natural celebratory pose, and polished event photography style.
Natural skin tones, realistic lighting, and high-detail textures.
Highly realistic, 4k, no distortion, no extra fingers, no face change.
""".strip(),
}

EVENT_PROMPTS_SOLO = {
    "wedding": """
A realistic portrait of the guest alone at an elegant wedding venue.
The guest must have the exact same face and identity as the reference image.
Do not include a bride or groom in the final image.
Natural pose, perfect lighting, soft shadows, and true-to-life skin tones.
Professional wedding photography, shallow depth of field.
Highly realistic, 4k, no distortion, no extra fingers, no face change.
""".strip(),
    "palestinian_henna": """
A realistic solo portrait of the guest at a Palestinian henna celebration.
The guest must have the exact same face and identity as the reference image.
Do not include additional people in the final image.
Include culturally respectful festive details and warm event lighting.
Highly realistic, 4k, no distortion, no extra fingers, no face change.
""".strip(),
    "graduation": """
A realistic solo graduation portrait of the guest.
The guest must have the exact same face and identity as the reference image.
Do not include additional people in the final image.
Include tasteful graduation context with natural celebratory styling.
Highly realistic, 4k, no distortion, no extra fingers, no face change.
""".strip(),
}


def _api_token() -> str:
    return os.getenv("REPLICATE_API_TOKEN") or getattr(settings, "REPLICATE_API_TOKEN", "")


def _model_ref() -> str:
    return (
        getattr(settings, "REPLICATE_INSTANTID_MODEL", None)
        or os.getenv("REPLICATE_INSTANTID_MODEL")
        or DEFAULT_INSTANTID_MODEL
    ).strip()


def _output_to_bytes(output: Any) -> bytes:
    if output is None:
        raise RuntimeError("Replicate returned no output.")

    first = output[0] if isinstance(output, (list, tuple)) else output

    if isinstance(first, (bytes, bytearray)):
        return bytes(first)

    if isinstance(first, str) and first.startswith("http"):
        r = requests.get(first, timeout=180)
        r.raise_for_status()
        return r.content

    read_fn = getattr(first, "read", None)
    if callable(read_fn):
        data = read_fn()
        if isinstance(data, str) and data.startswith("http"):
            r = requests.get(data, timeout=180)
            r.raise_for_status()
            return r.content
        if isinstance(data, (bytes, bytearray)):
            return bytes(data)

    url_fn = getattr(first, "url", None)
    if callable(url_fn):
        url = url_fn()
        if isinstance(url, str) and url.startswith("http"):
            r = requests.get(url, timeout=180)
            r.raise_for_status()
            return r.content

    if isinstance(first, str):
        r = requests.get(first, timeout=180)
        r.raise_for_status()
        return r.content

    raise RuntimeError(f"Unexpected Replicate output type: {type(first)!r}")


def generate_wedding_image_with_replicate(
    guest_image_path: str,
    bride_image_path: str | None,
    *,
    event_type: str | None = None,
    extra_prompt: str | None = None,
    include_bride: bool = True,
) -> bytes:
    """
    Run InstantID (or compatible) model on Replicate.

    Parameters
    ----------
    guest_image_path:
        Path to the guest face reference (e.g. rembg transparent PNG — still works as ID ref).
    bride_image_path:
        Path to bride reference; passed as ``pose_image`` for layout/composition guidance.
    extra_prompt:
        Optional text appended to the base wedding prompt (e.g. kiosk style hint).

    Returns
    -------
    bytes
        Raw image bytes from the model (may be WebP, JPEG, or PNG).

    Raises
    ------
    RuntimeError
        If API token is missing or Replicate fails.
    FileNotFoundError
        If paths are invalid.
    """
    token = _api_token()
    if not token:
        raise RuntimeError(
            "REPLICATE_API_TOKEN is not configured. Set it in your environment or Django settings."
        )

    guest_path = Path(guest_image_path).expanduser().resolve()
    bride_path: Path | None = None
    if not guest_path.is_file():
        raise FileNotFoundError(f"Guest image not found: {guest_path}")
    if include_bride:
        if not bride_image_path:
            raise FileNotFoundError("Bride image not found: no bride image path was provided.")
        bride_path = Path(bride_image_path).expanduser().resolve()
        if not bride_path.is_file():
            raise FileNotFoundError(f"Bride image not found: {bride_path}")

    model = _model_ref()
    prompt_map = EVENT_PROMPTS if include_bride else EVENT_PROMPTS_SOLO
    prompt = prompt_map.get((event_type or "").strip(), prompt_map["wedding"])
    if extra_prompt and extra_prompt.strip():
        prompt = f"{prompt}\n\nAdditional direction: {extra_prompt.strip()}"

    negative = os.getenv(
        "REPLICATE_NEGATIVE_PROMPT",
        "(lowres, low quality, worst quality:1.2), (text:1.2), watermark, painting, drawing, "
        "illustration, glitch, deformed, mutated, cross-eyed, ugly, disfigured, extra fingers, "
        "bad hands, duplicate faces",
    )
    try:
        guidance = float(os.getenv("REPLICATE_GUIDANCE_SCALE", "5"))
    except ValueError:
        guidance = 5.0

    sdxl_weights = os.getenv("REPLICATE_SDXL_WEIGHTS", "protovision-xl-high-fidel")

    guest_data = guest_path.read_bytes()

    input_payload: dict[str, Any] = {
        "image": BytesIO(guest_data),
        "prompt": prompt,
        "sdxl_weights": sdxl_weights,
        "guidance_scale": guidance,
        "negative_prompt": negative,
    }
    if include_bride:
        bride_data = bride_path.read_bytes()
        input_payload["pose_image"] = BytesIO(bride_data)

    client = replicate.Client(api_token=token)
    try:
        logger.info(
            "Replicate InstantID: model=%s guest=%s include_bride=%s bride=%s",
            model,
            guest_path,
            include_bride,
            bride_path,
        )
        output = client.run(model, input=input_payload)
    except Exception as e:
        logger.exception("Replicate run failed for model %s", model)
        raise RuntimeError(f"Replicate image generation failed: {e}") from e

    try:
        return _output_to_bytes(output)
    except Exception as e:
        logger.exception("Failed to interpret Replicate output")
        raise RuntimeError(f"Replicate output handling failed: {e}") from e
