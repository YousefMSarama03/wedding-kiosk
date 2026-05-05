"""
QR code generation for the photo download flow.

Guests scan the QR code to open the download URL and save their generated photo.
"""

from pathlib import Path

import qrcode
from django.conf import settings


def generate_qr_code(download_url: str, filename: str = None, subdir: str = "qrcodes") -> str:
    """
    Encode download_url into a QR image and save it under media/qrcodes/.

    Args:
        download_url: Full URL to encode (e.g. https://example.com/api/photos/5/download/).
        filename: Optional filename (e.g. photo_5.png). If omitted, a unique name is used.

    Returns:
        Path relative to MEDIA_ROOT (e.g. "qrcodes/photo_5.png") for building the media URL.
    """
    if not filename:
        import uuid
        filename = f"{uuid.uuid4().hex}.png"

    if not filename.lower().endswith(".png"):
        filename = f"{filename}.png"

    img = qrcode.make(download_url)
    media_root = Path(settings.MEDIA_ROOT)
    qr_dir = media_root / subdir
    qr_dir.mkdir(parents=True, exist_ok=True)
    filepath = qr_dir / filename
    img.save(str(filepath))

    return f"{subdir}/{filename}".replace("\\", "/")
