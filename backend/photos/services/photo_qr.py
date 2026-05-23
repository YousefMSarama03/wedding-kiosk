"""
Public download URL and QR materialization for a photo (works before AI finishes).
"""

from __future__ import annotations

from django.conf import settings
import os

from events.models import event_folder_name

from ..models import Photo
from .qr_service import generate_qr_code

__all__ = [
    "build_photo_download_absolute_url",
    "materialize_photo_qr",
]


def build_photo_download_absolute_url(photo_id: int, request=None) -> str:
    """
    Absolute URL for GET /api/photos/<id>/download/ (stable before ``generated_image`` exists).
    """
    path = f"/api/photos/{photo_id}/download/"
    public = getattr(settings, "PUBLIC_HOST", "").strip()
    if public:
        scheme = getattr(settings, "PUBLIC_SCHEME", "http")
        port = str(getattr(settings, "PUBLIC_PORT", "8000"))
        port_suffix = f":{port}" if port and port not in ("80", "443") else ""
        return f"{scheme}://{public}{port_suffix}{path}"
    if request is not None:
        return request.build_absolute_uri(path)
    base = getattr(settings, "API_PUBLIC_BASE_URL", "").strip().rstrip("/")
    if base:
        return f"{base}{path}"
    if getattr(settings, "DEBUG", False):
        port = getattr(settings, "PUBLIC_PORT", "") or os.getenv("PORT", "8000")
        port_suffix = f":{port}" if port and port not in ("80", "443") else ""
        return f"http://127.0.0.1{port_suffix}{path}"
    raise RuntimeError(
        "Set PUBLIC_HOST, API_PUBLIC_BASE_URL, or call with request to build download URLs."
    )


def materialize_photo_qr(photo_id: int, *, request=None) -> str:
    """
    Write QR PNG under media for this photo; same encoding as GET /qr/.
    Safe to call from Celery (pass request=None when PUBLIC_HOST or API_PUBLIC_BASE_URL is set).
    """
    photo = Photo.objects.get(pk=photo_id)
    download_url = build_photo_download_absolute_url(photo_id, request=request)
    return generate_qr_code(
        download_url,
        filename=f"photo_{photo_id}.png",
        subdir=f"events/{event_folder_name(photo.event)}/qrcodes",
    )
