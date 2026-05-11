"""
OpenAI-based wedding keepsake photo generation (legacy DALL-E path).

Guest-only: one input image + prompt (no bride/couple composition).
"""

import base64
import os
import tempfile
import uuid
from io import BytesIO

from django.conf import settings
from events.models import Event
from events.models import event_folder_name
from events.welcome_sign import welcome_sign_extra_prompt
from openai import OpenAI


def _client():
    api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Set it in your environment or Django settings."
        )
    return OpenAI(api_key=api_key)


EVENT_PROMPTS = {
    "wedding": """
Create a professional, photorealistic wedding portrait of this person alone at an elegant wedding venue.
Preserve this person’s identity and outfit exactly as provided.
Do not include additional people; keep the background as a tasteful wedding venue/stage.
Exposure/lighting: brighten the overall scene so the subject and venue are clear; soft venue lighting with realistic shadows (no harsh HDR glow).
Color: consistent white balance; natural skin tones.
Finish: looks like a real camera photo (no “AI” artifacts, no plastic/waxy skin, no over-sharpening).
Editorial wedding photography look: shallow depth of field, sharp focus on face.
""".strip(),
    "palestinian_henna": """
Create a professional, photorealistic Palestinian henna celebration portrait of this person alone.
Preserve this person’s identity and outfit exactly as provided.
Do not include additional people; keep the scene focused on the subject.
Background and environment only (not on the person): apply Palestinian heritage–inspired design to the backdrop and set dressing—respectful and tasteful, not stereotypical—such as keffiyeh-pattern drapery or wall textiles behind the subject, olive branches as subtle botanical accents, and Palestinian embroidery (tatreez) on distant cushions, table linens, wall hangings, or ceremonial props. Do not alter this person’s clothing or add heritage patterns to their outfit; preserve their outfit exactly as provided.
Warm festive henna-night atmosphere.
Exposure/lighting: brighten the overall scene so the subject and decor are clear; soft warm lighting with realistic shadows (no harsh HDR glow).
Color: consistent white balance; natural skin tones.
Finish: looks like a real camera photo (no “AI” artifacts, no plastic/waxy skin, no over-sharpening).
Professional event photography look: shallow depth of field, sharp focus on face.
""".strip(),
    "graduation": """
Create a professional, photorealistic graduation portrait of this person alone.
Preserve this person’s identity and outfit exactly as provided.
Do not include additional people; keep the scene focused on the subject.
Include tasteful graduation context (academic venue cues, celebratory styling) with clean composition.
Exposure/lighting: brighten the overall scene so the subject and background are clear; balanced exposure; soft realistic shadows.
Color: consistent white balance; natural skin tones.
Finish: looks like a real camera photo (no “AI” artifacts, no plastic/waxy skin, no over-sharpening).
Professional event photography look: shallow depth of field, sharp focus on face.
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
    *,
    event_type="wedding",
    event_id=None,
    event_bucket=None,
    style_fragment: str = "",
):
    """
    Generate a keepsake using DALL-E 2 edit: one image (guest) + prompt.

    API requirements (from OpenAI docs and community):
    - Edit endpoint often only accepts model="dall-e-2" (gpt-image-1 may be restricted).
    - Image must be sent with explicit content_type "image/png" or the API returns
      "unsupported mimetype (application/octet-stream)". Use a real file handle, not raw bytes.
    - Image must be square PNG, max 4MB. We convert via _ensure_png_square.
    """
    client = _client()

    guest_png = _ensure_png_square(guest_image_path)

    base_prompt = EVENT_PROMPTS.get(event_type, EVENT_PROMPTS["wedding"])
    event_obj = None
    if event_id is not None:
        event_obj = Event.objects.filter(pk=event_id).only(
            "bride_name", "groom_name", "wedding_date", "event_type"
        ).first()
    sign_extra = welcome_sign_extra_prompt(event_obj)
    bits = [base_prompt]
    if style_fragment.strip():
        bits.append(f"Additional direction: {style_fragment.strip()}")
    if sign_extra:
        bits.append(sign_extra)
    full_prompt = "\n\n".join(bits)

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    try:
        tmp.write(guest_png)
        tmp.close()
        with open(tmp.name, "rb") as f:
            result = client.images.edit(
                model="dall-e-2",
                prompt=full_prompt,
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
    if not event_bucket and event_obj is not None:
        event_bucket = event_folder_name(event_obj)
    if not event_bucket:
        event_bucket = "event_unknown"
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
    style="",
    *,
    event_id=None,
    event_bucket=None,
    event_type="wedding",
    model=None,
    output_relative=None,
):
    """Django-facing wrapper for the legacy OpenAI path."""
    if not os.path.isfile(guest_image_path):
        raise RuntimeError(f"Guest image not found: {guest_image_path}")

    return generate_wedding_photo(
        guest_image_path,
        event_id=event_id,
        event_bucket=event_bucket,
        event_type=event_type,
        style_fragment=style or "",
    )
