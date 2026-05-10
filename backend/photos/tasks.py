"""
Celery tasks: AI pipeline, then QR materialization (chain).
"""

from __future__ import annotations

import logging

from celery import shared_task
from django.db import close_old_connections

from .models import Photo
from .services.photo_ai_job import execute_photo_ai_processing, finalize_photo_guest_only
from .services.photo_qr import materialize_photo_qr

logger = logging.getLogger(__name__)


@shared_task(name="photos.process_photo_ai_task")
def process_photo_ai_task(photo_id: int) -> int:
    close_old_connections()
    try:
        photo = Photo.objects.get(pk=photo_id)
        if not photo.use_ai_generation:
            finalize_photo_guest_only(photo_id)
            return photo_id
        execute_photo_ai_processing(photo_id)
        return photo_id
    except Exception:
        logger.exception("process_photo_ai_task failed for photo_id=%s", photo_id)
        Photo.objects.filter(pk=photo_id).update(status=Photo.STATUS_PENDING)
        raise
    finally:
        close_old_connections()


@shared_task(name="photos.materialize_photo_qr_task")
def materialize_photo_qr_task(photo_id: int) -> None:
    """Second step in chain: write QR image after AI completes."""
    close_old_connections()
    try:
        materialize_photo_qr(photo_id, request=None)
    except Exception:
        logger.exception("materialize_photo_qr_task failed for photo_id=%s", photo_id)
        raise
    finally:
        close_old_connections()
