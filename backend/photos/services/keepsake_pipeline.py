"""
End-to-end keepsake pipeline: guest cutout → bride prep → Replicate InstantID → saved file.

No PIL merge of guest onto bride; the model generates the final scene from references.
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


def _prepare_bride_image(
    bride_path: Path,
    max_long_edge: int,
    out_path: Path,
) -> None:
    """
    Load bride photo, optionally downscale, save as PNG for Replicate pose/reference input.
    """
    if max_long_edge < 1:
        raise ValueError("bride_max_long_edge must be >= 1")

    with Image.open(bride_path) as im:
        im.load()
        if im.mode == "RGBA":
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[3])
            rgb = bg
        else:
            rgb = im.convert("RGB")
        w, h = rgb.size
        m = max(w, h)
        if m > max_long_edge:
            scale = max_long_edge / m
            nw = max(1, int(round(w * scale)))
            nh = max(1, int(round(h * scale)))
            rgb = rgb.resize((nw, nh), Image.Resampling.LANCZOS)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        rgb.save(out_path, format="PNG", optimize=True)


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
    bride_image_path: PathLike | None,
    *,
    event_id: int | None = None,
    event_type: str | None = None,
    merge_position: tuple[int, int] = (100, 120),
    max_guest_size: tuple[int, int] | None = (900, 1200),
    bride_max_long_edge: int = 2048,
    rembg_model: str = "u2net",
    rembg_alpha_matting: bool = False,
    skip_refinement: bool = False,
    refine_prompt: str | None = None,
    refinement_model: str | None = None,
    save_merged_intermediate: bool = False,
    include_bride: bool = True,
) -> KeepsakePipelineResult:
    """
    Pipeline:

    1. Remove background from the guest image (rembg).
    2. Prepare bride image (downscale if needed) as reference for Replicate.
    3. Unless ``skip_refinement``: call Replicate InstantID to generate the wedding photo.
       If ``skip_refinement``: save guest cutout flattened on white (no API call).
    4. Save final image under ``MEDIA_ROOT/generated/`` as PNG.

    Parameters ``merge_position``, ``max_guest_size``, and ``refinement_model`` are kept for
    backward compatibility and are ignored.

    Environment
    -----------
    ``REPLICATE_API_TOKEN`` (required unless ``skip_refinement`` is True).
    Optional: ``REPLICATE_INSTANTID_MODEL``, ``REPLICATE_GUIDANCE_SCALE``, ``REPLICATE_SDXL_WEIGHTS``,
    ``REPLICATE_NEGATIVE_PROMPT``.
    """
    if merge_position != (100, 120) or max_guest_size != (900, 1200) or refinement_model:
        logger.debug(
            "Keepsake: legacy merge/refinement kwargs ignored (merge_position=%s, max_guest_size=%s, refinement_model=%s)",
            merge_position,
            max_guest_size,
            refinement_model,
        )

    guest_path = Path(guest_image_path).expanduser().resolve()
    if not guest_path.is_file():
        raise FileNotFoundError(f"Guest image not found: {guest_path}")
    bride_path: Path | None = None
    if include_bride:
        if not bride_image_path:
            raise FileNotFoundError("Bride image not found: no bride image path was provided.")
        bride_path = Path(bride_image_path).expanduser().resolve()
        if not bride_path.is_file():
            raise FileNotFoundError(f"Bride image not found: {bride_path}")

    def _temp_png(suffix: str) -> Path:
        fd, path = tempfile.mkstemp(suffix=suffix, prefix="keepsake_")
        os.close(fd)
        return Path(path)

    tmp_guest = _temp_png("_guest_nobg.png")
    tmp_bride = _temp_png("_bride_prep.png") if include_bride else None
    temp_paths = [tmp_guest]
    if tmp_bride:
        temp_paths.append(tmp_bride)

    try:
        remove_background_to_png(
            guest_path,
            output_path=tmp_guest,
            model_name=rembg_model,
            alpha_matting=rembg_alpha_matting,
        )
        logger.info("Keepsake: guest background removed -> %s", tmp_guest)

        if include_bride:
            _prepare_bride_image(bride_path, bride_max_long_edge, tmp_bride)
            logger.info("Keepsake: bride prepared -> %s", tmp_bride)

        media = _media_root()
        event_bucket = f"event_{event_id}" if event_id is not None else "event_unknown"
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

        raw_bytes = generate_wedding_image_with_replicate(
            str(tmp_guest),
            str(tmp_bride) if tmp_bride else None,
            event_type=event_type,
            extra_prompt=refine_prompt,
            include_bride=include_bride,
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
