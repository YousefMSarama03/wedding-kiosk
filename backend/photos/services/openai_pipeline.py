"""
OpenAI-based wedding keepsake photo generation.

Uses two photos: guest (kiosk capture) and bride (wedding photo).
Places the guest next to the bride as a professional wedding keepsake.
"""

import base64
import os
import tempfile
import uuid
from io import BytesIO

from django.conf import settings
from openai import OpenAI

# Lazy client so Django settings are loaded (OPENAI_API_KEY may come from .env via settings)
def _client():
    api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Set it in your environment or Django settings."
        )
    return OpenAI(api_key=api_key)


EVENT_PROMPT_SINGLE = {
    "wedding": """
Place this person in a realistic wedding photo next to a bride on a wedding stage.
Keep their face and clothing unchanged.
Make it look like a professional wedding photograph.
""".strip(),
    "palestinian_henna": """
Place this person in a realistic Palestinian henna celebration portrait.
Keep their face and clothing unchanged.
Include tasteful and culturally respectful Palestinian henna party atmosphere and details.
Make it look like a professional event photograph.
""".strip(),
    "graduation": """
Place this person in a realistic graduation celebration portrait.
Keep their face and clothing unchanged.
Include tasteful graduation context and visual details.
Make it look like a professional event photograph.
""".strip(),
}

EVENT_PROMPT_SOLO = {
    "wedding": """
Place this person in a realistic wedding portrait at an elegant wedding venue.
Keep their face and clothing unchanged.
Do not include a bride or groom in the final image.
Make it look like a professional wedding photograph.
""".strip(),
    "palestinian_henna": """
Place this person in a realistic Palestinian henna celebration portrait.
Keep their face and clothing unchanged.
Do not include additional people in the final image.
Include tasteful and culturally respectful Palestinian henna party atmosphere and details.
Make it look like a professional event photograph.
""".strip(),
    "graduation": """
Place this person in a realistic graduation portrait.
Keep their face and clothing unchanged.
Do not include additional people in the final image.
Include tasteful graduation context and visual details.
Make it look like a professional event photograph.
""".strip(),
}


def _ensure_png_square(file_path, size=1024):
    """Load image, convert to RGBA, crop/resize to square, return PNG bytes. Required for DALL-E 2."""
    from PIL import Image
    img = Image.open(file_path)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    w, h = img.size
    if w != size or h != size:
        if w != h:
            side = min(w, h)
            left = (w - side) // 2
            top = (h - side) // 2
            img = img.crop((left, top, left + side, top + side))
        img = img.resize((size, size), Image.Resampling.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_wedding_photo(
    guest_image_path,
    bride_image_path,
    *,
    event_type="wedding",
    event_id=None,
    include_bride=True,
):
    """
    Generate a wedding keepsake by placing the guest in a wedding scene.
    Uses DALL-E 2 edit: one image (guest) + prompt. Bride image path is kept for API compatibility.

    API requirements (from OpenAI docs and community):
    - Edit endpoint often only accepts model="dall-e-2" (gpt-image-1 may be restricted).
    - Image must be sent with explicit content_type "image/png" or the API returns
      "unsupported mimetype (application/octet-stream)". Use a real file handle, not raw bytes.
    - Image must be square PNG, max 4MB. We convert via _ensure_png_square.
    """
    client = _client()

    # DALL-E 2 requires a single PNG image (square, max 4MB). Convert guest to PNG square.
    guest_png = _ensure_png_square(guest_image_path)

    # Write to temp file and pass as file object with explicit image/png so the API
    # does not reject with "unsupported mimetype (application/octet-stream)".
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    try:
        tmp.write(guest_png)
        tmp.close()
        with open(tmp.name, "rb") as f:
            result = client.images.edit(
                model="dall-e-2",
                prompt=(
                    EVENT_PROMPT_SINGLE if include_bride else EVENT_PROMPT_SOLO
                ).get(event_type, (EVENT_PROMPT_SINGLE if include_bride else EVENT_PROMPT_SOLO)["wedding"]),
                image=("guest.png", f, "image/png"),
                size="1024x1024",
                n=1,
                response_format="b64_json",
            )
    except Exception as e:
        raise RuntimeError(f"OpenAI image request failed: {e}") from e
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    if not result or not getattr(result, "data", None) or not result.data:
        raise RuntimeError("OpenAI returned no image.")

    image_base64 = result.data[0].b64_json
    if not image_base64:
        raise RuntimeError("OpenAI returned empty image data.")
    image_bytes = base64.b64decode(image_base64)

    media_root = getattr(settings, "MEDIA_ROOT", "media")
    event_bucket = f"event_{event_id}" if event_id is not None else "event_unknown"
    generated_dir = os.path.join(media_root, "events", event_bucket, "generated")
    os.makedirs(generated_dir, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.png"
    output_path = os.path.join(generated_dir, filename)
    relative_path = os.path.join("events", event_bucket, "generated", filename).replace("\\", "/")

    with open(output_path, "wb") as f:
        f.write(image_bytes)

    return relative_path


def generate_wedding_with_openai(
    guest_image_path,
    bride_image_path,
    style="",
    *,
    event_id=None,
    event_type="wedding",
    model=None,
    output_relative=None,
    include_bride=True,
):
    """
    Django-facing wrapper: same signature for views.
    """
    if not os.path.isfile(guest_image_path):
        raise RuntimeError(f"Guest image not found: {guest_image_path}")
    if include_bride and (not bride_image_path or not os.path.isfile(bride_image_path)):
        raise RuntimeError(f"Bride image not found: {bride_image_path}")

    return generate_wedding_photo(
        guest_image_path,
        bride_image_path,
        event_id=event_id,
        event_type=event_type,
        include_bride=include_bride,
    )
