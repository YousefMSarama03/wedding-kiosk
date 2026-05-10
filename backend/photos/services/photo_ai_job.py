"""
Run the AI keepsake pipeline for a Photo row (sync or Celery worker).
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile

from events.models import event_folder_name

from ..models import Photo
from .keepsake_pipeline import run_keepsake_pipeline
from .openai_pipeline import generate_wedding_with_openai

logger = logging.getLogger(__name__)

__all__ = ["execute_photo_ai_processing", "finalize_photo_guest_only"]


def finalize_photo_guest_only(photo_id: int) -> None:
    """
    Copy ``guest_image`` into ``events/.../generated/`` (same layout as AI output),
    set ``generated_image`` and ``status=completed``.
    """
    photo = Photo.objects.get(pk=photo_id)
    if photo.generated_image and photo.generated_image.name:
        if photo.status != Photo.STATUS_COMPLETED:
            photo.status = Photo.STATUS_COMPLETED
            photo.save(update_fields=["status"])
        logger.info("Photo %s: guest-only already has generated -> %s", photo_id, photo.generated_image.name)
        return

    guest = photo.guest_image
    if not guest or not guest.name:
        raise ValueError("Guest image missing")

    guest_path = Path(guest.path)
    if not guest_path.is_file():
        raise FileNotFoundError(f"Guest image not found: {guest_path}")

    data = guest_path.read_bytes()
    ext = guest_path.suffix.lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        ext = ".jpg"
    out_name = f"{uuid.uuid4().hex}{ext}"

    photo.generated_image.save(out_name, ContentFile(data), save=False)
    photo.status = Photo.STATUS_COMPLETED
    photo.save(update_fields=["generated_image", "status"])
    logger.info("Photo %s: guest-only saved to generated -> %s", photo_id, photo.generated_image.name)


def execute_photo_ai_processing(photo_id: int) -> str:
    """
    Run pipeline; set ``generated_image`` and ``status=completed``.
    Caller must set ``processing`` before calling.
    """
    photo = Photo.objects.get(pk=photo_id)

    if not photo.use_ai_generation:
        raise ValueError("Photo is guest-only (use_ai_generation=False); AI pipeline must not run.")

    if photo.generated_image and photo.status == Photo.STATUS_COMPLETED:
        return photo.generated_image.name

    guest_path = photo.guest_image.path
    event_bucket = event_folder_name(photo.event)
    style_text = (photo.style or "").strip()

    if getattr(settings, "KEEPSAKE_USE_OPENAI_LEGACY", False):
        relative_path = generate_wedding_with_openai(
            guest_path,
            style_text,
            event_id=photo.event_id,
            event_bucket=event_bucket,
            event_type=getattr(photo.event, "event_type", "wedding"),
        )
    else:
        ks = run_keepsake_pipeline(
            Path(guest_path),
            event_id=photo.event_id,
            event_bucket=event_bucket,
            event_type=getattr(photo.event, "event_type", "wedding"),
            refine_prompt=style_text or None,
        )
        relative_path = ks.final_relative_path

    relative_path = relative_path.replace("\\", "/")
    photo.generated_image.name = relative_path
    photo.status = Photo.STATUS_COMPLETED
    photo.save(update_fields=["generated_image", "status"])
    logger.info("Photo %s: AI pipeline complete -> %s", photo_id, relative_path)
    return relative_path
