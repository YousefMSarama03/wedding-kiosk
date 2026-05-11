"""
Replicate image generation for wedding keepsake images.

Default model is OpenAI GPT Image 2 (text + multi-reference images).
Set REPLICATE_MODEL to a zsxkib/instant-id version hash to use the legacy InstantID path
(identity embedding), which uses a different API schema.

Guest-only composition (no bride/couple mode).
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
from PIL import Image

logger = logging.getLogger(__name__)

__all__ = ["generate_wedding_image_with_replicate", "EVENT_PROMPTS"]

# Default: OpenAI GPT Image 2 on Replicate. Override via REPLICATE_MODEL or REPLICATE_INSTANTID_MODEL.
DEFAULT_REPLICATE_MODEL = "openai/gpt-image-2"

# Legacy InstantID (only used if REPLICATE_MODEL points at instant-id).
DEFAULT_INSTANTID_MODEL = (
    "zsxkib/instant-id:2e4785a4d80dadf580077b2244c8d7c05d8e3faac04a04c02d8e099dd2876789"
)

EVENT_PROMPTS = {
    "wedding": """
Professional, photorealistic wedding portrait of the guest alone at an elegant wedding venue.
Preserve the guest exactly as in the reference image (identity/face/hair/beard/skin tone/body) and preserve the outfit exactly (clothing and accessories).
Do not include additional people; keep the background as a tasteful wedding venue/stage.
Natural confident pose that shows outfit details; correct proportions and anatomy.
Lighting: soft, realistic venue lighting; match light direction; brighten the overall exposure so the subject and venue are clear; subtle shadows; balanced highlights and shadow detail.
Color: consistent white balance; natural skin tones; gentle highlight rolloff.
Camera: editorial wedding photography, 50mm look, shallow depth of field, sharp focus on face.
Finish: looks like a real camera photo (no “AI” artifacts, no plastic/waxy skin, no over-sharpening); clean edges with no halos or color fringing at hair or clothing.
High realism and detail; avoid distortions and extra limbs/fingers; keep faces consistent.
""".strip(),
    "palestinian_henna": """
Professional, photorealistic solo portrait of the guest at a Palestinian henna celebration.
Preserve the guest exactly as in the reference image (identity/face/hair/beard/skin tone/body) and preserve the outfit exactly (clothing and accessories).
Do not include additional people; keep the scene focused on the guest.
Background and environment only (not on the guest): style the backdrop and scene props with Palestinian heritage–inspired design—culturally respectful, tasteful, not caricature—such as keffiyeh-pattern drapery or wall textiles behind the subject, olive branches as subtle botanical accents in the set, and Palestinian embroidery (tatreez) on distant cushions, table linens, wall hangings, or ceremonial textiles. Do not change, overlay, or add heritage patterns to the guest’s clothing or accessories; preserve their outfit exactly as in the reference image.
Warm henna-night ambiance with festive lighting and authentic-feeling decor.
Lighting: warm event lighting with soft shadows; brighten the scene so the subject and decor are clear; match light direction; balanced exposure without muddy shadows.
Color: consistent white balance; natural skin tones; realistic saturation.
Camera: professional event photography, shallow depth of field, crisp focus on face.
Finish: looks like a real camera photo (no “AI” artifacts, no plastic/waxy skin, no over-sharpening); precise subject edges without spill or fringe.
High realism and detail; avoid distortions and extra limbs/fingers; keep faces consistent.
""".strip(),
    "graduation": """
Professional, photorealistic solo graduation portrait of the guest.
Preserve the guest exactly as in the reference image (identity/face/hair/beard/skin tone/body) and preserve the outfit exactly (clothing and accessories).
Do not include additional people; keep the scene focused on the guest.
Scene: tasteful graduation context (academic venue cues, celebratory styling), clean composition.
Lighting: realistic and flattering; balanced exposure; brighten the overall scene so the subject and background look clear and well-lit; soft shadows; natural contrast.
Color: consistent white balance; natural skin tones; coherent color across subject and background.
Camera: polished event photography, shallow depth of field, crisp focus on face.
Finish: looks like a real camera photo (no “AI” artifacts, no plastic/waxy skin, no over-sharpening); clean compositing edges.
High realism and detail; avoid distortions and extra limbs/fingers; keep faces consistent.
""".strip(),
}


def _api_token() -> str:
    return os.getenv("REPLICATE_API_TOKEN") or getattr(settings, "REPLICATE_API_TOKEN", "")


def _model_ref() -> str:
    ref = (
        getattr(settings, "REPLICATE_MODEL", None)
        or os.getenv("REPLICATE_MODEL")
        or getattr(settings, "REPLICATE_INSTANTID_MODEL", None)
        or os.getenv("REPLICATE_INSTANTID_MODEL")
        or DEFAULT_REPLICATE_MODEL
    )
    return (ref or DEFAULT_REPLICATE_MODEL).strip()


def _is_instantid_model(model: str) -> bool:
    m = model.lower()
    return "instant-id" in m or "instantid" in m


def _is_gpt_image_2_model(model: str) -> bool:
    m = model.lower().strip()
    return m.startswith("openai/gpt-image-2") or "gpt-image-2" in m


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


def _flux_bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("true", "1", "yes", "on")


def _flux_input_payload(*, prompt: str, guest_data: bytes) -> dict[str, Any]:
    """
    FLUX.2 [pro] schema (Replicate). No negative_prompt — model docs recommend positive prompts only.
    """
    input_images: list[BytesIO] = [BytesIO(guest_data)]

    resolution = os.getenv("REPLICATE_FLUX_RESOLUTION", "2 MP").strip() or "2 MP"
    aspect_ratio = os.getenv("REPLICATE_FLUX_ASPECT_RATIO", "match_input_image").strip() or "match_input_image"
    output_format = os.getenv("REPLICATE_FLUX_OUTPUT_FORMAT", "png").strip() or "png"
    try:
        output_quality = int(os.getenv("REPLICATE_FLUX_OUTPUT_QUALITY", "95"))
    except ValueError:
        output_quality = 95
    output_quality = max(0, min(100, output_quality))
    try:
        safety_tolerance = int(os.getenv("REPLICATE_FLUX_SAFETY_TOLERANCE", "2"))
    except ValueError:
        safety_tolerance = 2
    safety_tolerance = max(1, min(5, safety_tolerance))

    payload: dict[str, Any] = {
        "prompt": prompt,
        "input_images": input_images,
        "resolution": resolution,
        "aspect_ratio": aspect_ratio,
        "output_format": output_format,
        "output_quality": output_quality,
        "safety_tolerance": safety_tolerance,
        "prompt_upsampling": _flux_bool_env("REPLICATE_FLUX_PROMPT_UPSAMPLING", False),
    }

    seed_raw = os.getenv("REPLICATE_FLUX_SEED", "").strip()
    if seed_raw:
        try:
            payload["seed"] = int(seed_raw)
        except ValueError:
            pass

    if aspect_ratio == "custom":
        try:
            w = int(os.getenv("REPLICATE_FLUX_WIDTH", "0"))
            h = int(os.getenv("REPLICATE_FLUX_HEIGHT", "0"))
            if w > 0 and h > 0:
                payload["width"] = w
                payload["height"] = h
        except ValueError:
            pass

    return payload


def _prepare_image_bytes_for_gpt_image_2(raw: bytes) -> bytes:
    """
    GPT Image 2 on Replicate often fails on transparent PNGs; flatten onto white.
    Optional downscale via ``REPLICATE_GPT_IMAGE_MAX_INPUT_LONG_EDGE`` (0 / empty = off).
    """
    max_edge_raw = os.getenv("REPLICATE_GPT_IMAGE_MAX_INPUT_LONG_EDGE", "").strip().lower()
    try:
        max_long = 0 if max_edge_raw in ("", "0", "none", "off") else int(max_edge_raw)
    except ValueError:
        max_long = 0

    with Image.open(BytesIO(raw)) as im:
        im.load()
        rgba = im.convert("RGBA")
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.split()[3])
        rgb = bg
        if max_long > 0:
            w, h = rgb.size
            m = max(w, h)
            if m > max_long:
                scale = max_long / m
                rgb = rgb.resize(
                    (max(1, int(round(w * scale))), max(1, int(round(h * scale)))),
                    Image.Resampling.LANCZOS,
                )
        out = BytesIO()
        rgb.save(out, format="PNG", optimize=True)
        return out.getvalue()


def _gpt_image_2_input_payload(*, prompt: str, guest_data: bytes) -> dict[str, Any]:
    """
    openai/gpt-image-2 schema (Replicate).
    Docs: https://replicate.com/openai/gpt-image-2/readme
    """
    guest_prep = _prepare_image_bytes_for_gpt_image_2(guest_data)
    input_images: list[BytesIO] = [BytesIO(guest_prep)]

    aspect_ratio = os.getenv("REPLICATE_GPT_IMAGE_ASPECT_RATIO", "3:2").strip() or "3:2"
    quality = os.getenv("REPLICATE_GPT_IMAGE_QUALITY", "auto").strip() or "auto"
    output_format = os.getenv("REPLICATE_GPT_IMAGE_OUTPUT_FORMAT", "png").strip() or "png"
    background = os.getenv("REPLICATE_GPT_IMAGE_BACKGROUND", "opaque").strip() or "opaque"
    moderation = os.getenv("REPLICATE_GPT_IMAGE_MODERATION", "auto").strip() or "auto"
    try:
        number_of_images = int(os.getenv("REPLICATE_GPT_IMAGE_NUMBER_OF_IMAGES", "1"))
    except ValueError:
        number_of_images = 1
    number_of_images = max(1, min(10, number_of_images))

    return {
        "prompt": prompt,
        "input_images": input_images,
        "aspect_ratio": aspect_ratio,
        "quality": quality,
        "number_of_images": number_of_images,
        "output_format": output_format,
        "background": background,
        "moderation": moderation,
    }


def _instantid_input_payload(
    *,
    prompt: str,
    negative: str,
    guidance: float,
    sdxl_weights: str,
    guest_data: bytes,
) -> dict[str, Any]:
    return {
        "image": BytesIO(guest_data),
        "prompt": prompt,
        "sdxl_weights": sdxl_weights,
        "guidance_scale": guidance,
        "negative_prompt": negative,
    }


def generate_wedding_image_with_replicate(
    guest_image_path: str,
    *,
    event_type: str | None = None,
    extra_prompt: str | None = None,
) -> bytes:
    """
    Run Replicate image generation for a guest-only keepsake (default: GPT Image 2).

    Parameters
    ----------
    guest_image_path:
        Path to the guest reference (e.g. rembg cutout).
    extra_prompt:
        Optional text appended to the base prompt (e.g. kiosk style hint).

    Returns
    -------
    bytes
        Raw image bytes from the model (may be WebP, JPEG, or PNG).

    Raises
    ------
    RuntimeError
        If API token is missing or Replicate fails.
    FileNotFoundError
        If the guest path is invalid.
    """
    token = _api_token()
    if not token:
        raise RuntimeError(
            "REPLICATE_API_TOKEN is not configured. Set it in your environment or Django settings."
        )

    guest_path = Path(guest_image_path).expanduser().resolve()
    if not guest_path.is_file():
        raise FileNotFoundError(f"Guest image not found: {guest_path}")

    model = _model_ref()
    use_instantid = _is_instantid_model(model)
    use_gpt_image_2 = _is_gpt_image_2_model(model)

    prompt = EVENT_PROMPTS.get((event_type or "").strip(), EVENT_PROMPTS["wedding"])
    if extra_prompt and extra_prompt.strip():
        prompt = f"{prompt}\n\nAdditional direction: {extra_prompt.strip()}"

    guest_data = guest_path.read_bytes()

    if use_instantid:
        negative = os.getenv(
            "REPLICATE_NEGATIVE_PROMPT",
            "(lowres, low quality, worst quality:1.2), (text:1.2), watermark, painting, drawing, "
            "illustration, glitch, deformed, mutated, cross-eyed, ugly, disfigured, extra fingers, "
            "bad hands, duplicate faces, different person, different face, face swap, identity drift, "
            "new haircut, changed hairstyle, changed clothing, wardrobe change, makeup change",
        )
        try:
            guidance = float(os.getenv("REPLICATE_GUIDANCE_SCALE", "5"))
        except ValueError:
            guidance = 5.0
        sdxl_weights = os.getenv("REPLICATE_SDXL_WEIGHTS", "protovision-xl-high-fidel")
        input_payload = _instantid_input_payload(
            prompt=prompt,
            negative=negative,
            guidance=guidance,
            sdxl_weights=sdxl_weights,
            guest_data=guest_data,
        )
    elif use_gpt_image_2:
        intro = (
            "Image 1 is the guest. Create a single photorealistic event portrait following the "
            "scene description. Preserve the guest’s identity and outfit exactly as in image 1.\n\n"
        )
        input_payload = _gpt_image_2_input_payload(
            prompt=intro + prompt,
            guest_data=guest_data,
        )
    else:
        flux_intro = (
            "Image 1 is the guest. Create one photorealistic image following the scene "
            "description. Preserve their exact face, skin, clothing, hair, and accessories "
            "from image 1. Describe only what should appear.\n\n"
        )
        input_payload = _flux_input_payload(
            prompt=flux_intro + prompt,
            guest_data=guest_data,
        )

    client = replicate.Client(api_token=token)
    try:
        logger.info(
            "Replicate: model=%s backend=%s guest=%s",
            model,
            "instantid" if use_instantid else ("gpt-image-2" if use_gpt_image_2 else "flux"),
            guest_path,
        )
        output = client.run(model, input=input_payload)
    except Exception as e:
        logger.exception("Replicate run failed for model %s", model)
        msg = str(e).strip()
        if msg.endswith("Failed to generate:") or msg.endswith("Failed to generate"):
            msg += (
                " (Common causes: moderation — try REPLICATE_GPT_IMAGE_MODERATION=low in .env; "
                "oversized input — set REPLICATE_GPT_IMAGE_MAX_INPUT_LONG_EDGE=2048; or a bad "
                "request for the chosen model.)"
            )
        raise RuntimeError(f"Replicate image generation failed: {msg}") from e

    try:
        return _output_to_bytes(output)
    except Exception as e:
        logger.exception("Failed to interpret Replicate output")
        raise RuntimeError(f"Replicate output handling failed: {e}") from e
