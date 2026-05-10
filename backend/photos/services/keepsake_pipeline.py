"""
End-to-end keepsake pipeline: guest cutout → Replicate (GPT Image 2 by default) → saved file.

Guest-only scene generation from references (no bride/couple composition).
"""

from __future__ import annotations

import logging
import os
import tempfile
import uuid
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Union

from django.conf import settings
from events.models import Event
from events.models import event_folder_name
from events.welcome_sign import welcome_sign_extra_prompt
from PIL import Image

from .background_removal import remove_background_to_png
from .replicate_service import generate_wedding_image_with_replicate

logger = logging.getLogger(__name__)

PathLike = Union[str, Path]

__all__ = [
    "KeepsakePipelineResult",
    "run_keepsake_pipeline",
    "keepsake_pipeline_result_to_absolute_url",
]


@dataclass
class KeepsakePipelineResult:
    """Output of :func:`run_keepsake_pipeline`."""

    final_relative_path: str
    """Path under ``MEDIA_ROOT`` to the final image (e.g. ``generated/uuid.png``)."""

    merged_relative_path: str | None = None
    """If ``save_merged_intermediate`` is True, path to the guest cutout under ``processed/``."""


def _media_root() -> Path:
    return Path(getattr(settings, "MEDIA_ROOT", "media"))


def _flatten_rgba_to_rgb_png(rgba_path: Path) -> bytes:
    with Image.open(rgba_path) as im:
        im.load()
        rgba = im.convert("RGBA")
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.split()[3])
        buf = BytesIO()
        bg.save(buf, format="PNG", optimize=True)
        return buf.getvalue()


def run_keepsake_pipeline(
    guest_image_path: PathLike,
    *,
    event_id: int | None = None,
    event_bucket: str | None = None,
    event_type: str | None = None,
    rembg_model: str = "u2net",
    rembg_alpha_matting: bool = False,
    skip_refinement: bool = False,
    refine_prompt: str | None = None,
    refinement_model: str | None = None,
    save_merged_intermediate: bool = False,
) -> KeepsakePipelineResult:
    """
    Pipeline:

    1. Remove background from the guest image (rembg).
    2. Unless ``skip_refinement``: call Replicate (default ``openai/gpt-image-2``) to generate the scene.
       If ``skip_refinement``: save guest cutout flattened on white (no API call).
    3. Save final image under ``MEDIA_ROOT/generated/`` as PNG.

    Environment
    -----------
    ``REPLICATE_API_TOKEN`` (required unless ``skip_refinement`` is True).
    Model: ``REPLICATE_MODEL`` (defaults to ``openai/gpt-image-2``), or legacy ``REPLICATE_INSTANTID_MODEL``
    for InstantID (``zsxkib/instant-id:…``).
    InstantID-only: ``REPLICATE_GUIDANCE_SCALE``, ``REPLICATE_SDXL_WEIGHTS``, ``REPLICATE_NEGATIVE_PROMPT``.
    FLUX-only: ``REPLICATE_FLUX_RESOLUTION``, ``REPLICATE_FLUX_ASPECT_RATIO``, ``REPLICATE_FLUX_OUTPUT_FORMAT``,
    ``REPLICATE_FLUX_OUTPUT_QUALITY``, ``REPLICATE_FLUX_SAFETY_TOLERANCE``, ``REPLICATE_FLUX_PROMPT_UPSAMPLING``,
    ``REPLICATE_FLUX_SEED`` (optional).
    GPT Image 2-only: ``REPLICATE_GPT_IMAGE_ASPECT_RATIO``, ``REPLICATE_GPT_IMAGE_QUALITY``,
    ``REPLICATE_GPT_IMAGE_NUMBER_OF_IMAGES``, ``REPLICATE_GPT_IMAGE_OUTPUT_FORMAT``,
    ``REPLICATE_GPT_IMAGE_BACKGROUND``, ``REPLICATE_GPT_IMAGE_MODERATION``,
    ``REPLICATE_GPT_IMAGE_MAX_INPUT_LONG_EDGE`` (optional downscale; 0 = off).

    Welcome sign in generated scene: ``KEEPSAKE_WELCOME_SIGN`` (true/false); uses event names,
    date, and type via ``events.welcome_sign``.
    """
    if refinement_model:
        logger.debug("Keepsake: legacy refinement_model ignored (%s)", refinement_model)

    guest_path = Path(guest_image_path).expanduser().resolve()
    if not guest_path.is_file():
        raise FileNotFoundError(f"Guest image not found: {guest_path}")

    def _temp_png(suffix: str) -> Path:
        fd, path = tempfile.mkstemp(suffix=suffix, prefix="keepsake_")
        os.close(fd)
        return Path(path)

    tmp_guest = _temp_png("_guest_nobg.png")
    temp_paths = [tmp_guest]

    try:
        event_obj: Event | None = None
        if event_id is not None:
            event_obj = Event.objects.filter(pk=event_id).only(
                "bride_name", "groom_name", "wedding_date", "event_type"
            ).first()

        remove_background_to_png(
            guest_path,
            output_path=tmp_guest,
            model_name=rembg_model,
            alpha_matting=rembg_alpha_matting,
        )
        logger.info("Keepsake: guest background removed -> %s", tmp_guest)

        media = _media_root()
        if not event_bucket and event_obj is not None:
            event_bucket = event_folder_name(event_obj)
        if not event_bucket:
            event_bucket = "event_unknown"
        generated = media / "events" / event_bucket / "generated"
        generated.mkdir(parents=True, exist_ok=True)

        merged_rel: str | None = None
        if save_merged_intermediate:
            proc_dir = media / "events" / event_bucket / "processed"
            proc_dir.mkdir(parents=True, exist_ok=True)
            guest_name = f"guest_nobg_{uuid.uuid4().hex}.png"
            guest_abs = proc_dir / guest_name
            guest_abs.write_bytes(tmp_guest.read_bytes())
            merged_rel = f"events/{event_bucket}/processed/{guest_name}"

        final_name = f"{uuid.uuid4().hex}.png"
        final_abs = generated / final_name
        rel = f"events/{event_bucket}/generated/{final_name}"

        if skip_refinement:
            flat = _flatten_rgba_to_rgb_png(tmp_guest)
            final_abs.write_bytes(flat)
            logger.info("Keepsake: skip_refinement, saved flattened guest -> %s", final_abs)
            return KeepsakePipelineResult(
                final_relative_path=rel,
                merged_relative_path=merged_rel,
            )

        sign_extra = welcome_sign_extra_prompt(event_obj)
        prompt_bits = [p for p in (refine_prompt, sign_extra) if p and str(p).strip()]
        combined_refine = "\n\n".join(prompt_bits) if prompt_bits else None

        raw_bytes = generate_wedding_image_with_replicate(
            str(tmp_guest),
            event_type=event_type,
            extra_prompt=combined_refine,
        )
        with Image.open(BytesIO(raw_bytes)) as out_im:
            out_im.load()
            rgb_final = out_im.convert("RGB")
            rgb_final.save(final_abs, format="PNG", optimize=True)
        logger.info("Keepsake: Replicate complete -> %s", final_abs)

        return KeepsakePipelineResult(
            final_relative_path=rel,
            merged_relative_path=merged_rel,
        )
    finally:
        for p in temp_paths:
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass


def keepsake_pipeline_result_to_absolute_url(
    result: KeepsakePipelineResult,
    *,
    build_absolute_uri=None,
) -> dict[str, str | None]:
    """
    Build URL paths for use in DRF responses (relative ``/media/...`` or absolute if request given).

    If ``build_absolute_uri`` is a callable (e.g. ``request.build_absolute_uri``), returns
    absolute URLs; otherwise returns paths starting with ``/media/``.
    """
    media_url = getattr(settings, "MEDIA_URL", "/media/").rstrip("/") + "/"

    def _url(rel: str | None) -> str | None:
        if not rel:
            return None
        path = f"{media_url}{rel.replace(chr(92), '/')}"
        if build_absolute_uri:
            return build_absolute_uri(path)
        return path

    return {
        "final_url": _url(result.final_relative_path),
        "merged_url": _url(result.merged_relative_path),
    }
