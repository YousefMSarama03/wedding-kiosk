"""
API views for photos.
Uses DRF generic views: list/create and a custom view for AI processing.
"""

import base64
import uuid
from pathlib import Path

from django.core.files.base import ContentFile
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from django.conf import settings
from events.models import Event, Bride
from .models import Photo
from .serializers import PhotoSerializer
from .services.keepsake_pipeline import run_keepsake_pipeline
from .services.openai_pipeline import generate_wedding_with_openai
from .services.qr_service import generate_qr_code


# GET /api/photos/  -> list all photos
# POST /api/photos/ -> create a photo (send event id, guest_image file; status set to pending on model)
class PhotoListCreateView(generics.ListCreateAPIView):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        event = serializer.validated_data["event"]
        if event.at_photo_limit():
            n = event.photos.count()
            raise ValidationError(
                [
                    f"This event has reached its photo limit ({n} / {event.max_photos} photos).",
                ]
            )
        serializer.save()


# GET /api/photos/<id>/  -> retrieve one photo
# DELETE /api/photos/<id>/ -> delete photo
@method_decorator(csrf_exempt, name="dispatch")
class PhotoDetailView(generics.RetrieveDestroyAPIView):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    authentication_classes = []
    permission_classes = [AllowAny]


# POST /api/photos/capture/
# For kiosk: accept base64 image from camera (e.g. canvas.toDataURL()), decode and save as guest_image.
@method_decorator(csrf_exempt, name="dispatch")
class PhotoCaptureView(APIView):
    """
    Create a photo from a base64-encoded image (e.g. from tablet camera / getDisplayMedia).
    Request body: event_id, style (optional), image_base64 (with or without data URL prefix).
    Image is decoded -> ContentFile -> saved under media/guests/ as guest_image; status = pending.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        event_id = request.data.get("event_id")
        if event_id is None:
            return Response(
                {"error": "event_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        event = get_object_or_404(Event, pk=event_id)

        if event.at_photo_limit():
            return Response(
                {
                    "error": (
                        f"This event has reached its photo limit ({event.max_photos} photos). "
                        "Ask staff to raise the limit or choose another event."
                    ),
                    "max_photos": event.max_photos,
                    "current_photos": event.photos.count(),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        raw = request.data.get("image_base64")
        if not raw:
            return Response(
                {"error": "image_base64 is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Support both raw base64 and data URL (e.g. "data:image/jpeg;base64,/9j/4AAQ...").
        # Strip the prefix so we only pass the base64 payload to b64decode.
        if raw.startswith("data:"):
            raw = raw.split(",", 1)[-1]
        try:
            image_bytes = base64.b64decode(raw)
        except Exception as e:
            return Response(
                {"error": f"Invalid base64 image: {e!s}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not image_bytes:
            return Response(
                {"error": "Decoded image is empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ContentFile wraps bytes so ImageField can save to media/guests/ (upload_to on guest_image).
        filename = f"capture_{uuid.uuid4().hex}.jpg"
        content = ContentFile(image_bytes, name=filename)

        style = request.data.get("style") or ""

        photo = Photo.objects.create(
            event=event,
            guest_image=content,
            style=style,
            status=Photo.STATUS_PENDING,
            is_approved=True,
            is_featured=False,
            is_hidden=False,
        )

        return Response(
            {"photo_id": photo.id, "status": photo.status},
            status=status.HTTP_201_CREATED,
        )


# POST /api/photos/{id}/process-ai/
# OpenAI-based pipeline: status=processing -> OpenAI generate_wedding_with_openai() -> save to generated_image.
@method_decorator(csrf_exempt, name="dispatch")
class PhotoProcessAIView(APIView):
    """
    Trigger AI processing for a photo.

    By default runs the keepsake pipeline (rembg → bride prep → Replicate InstantID).
    Set ``KEEPSAKE_USE_OPENAI_LEGACY=true`` to use the legacy OpenAI DALL-E path instead
    (``OPENAI_API_KEY`` only; guest image only).

    Flow:
    - set status=processing
    - call pipeline → save path into generated_image
    - set status=completed
    If any error occurs, status is set back to pending.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, pk):
        photo = get_object_or_404(Photo, pk=pk)
        raw_include_bride = request.data.get("include_bride", True)
        include_bride = str(raw_include_bride).strip().lower() not in {"false", "0", "no", "off"}

        # Optionally update style from request payload before processing.
        style = request.data.get("style")
        if style is not None:
            photo.style = style
            photo.save(update_fields=["style"])

        # 1. Mark as processing so the kiosk can show a loading state.
        photo.status = Photo.STATUS_PROCESSING
        photo.save(update_fields=["status"])

        # 2. Optional bride image: include for "with bride", skip for "user only".
        bride_path = None
        if include_bride:
            bride = Bride.objects.filter(active=True).first()
            if bride and bride.image:
                bride_path = bride.image.path
            else:
                event = photo.event
                if not event.bride_image:
                    photo.status = Photo.STATUS_PENDING
                    photo.save(update_fields=["status"])
                    return Response(
                        {"error": "Active bride image not configured. Add one in Admin -> Brides or set the event's bride image."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                bride_path = event.bride_image.path

        guest_path = photo.guest_image.path

        # 3. Generate: Replicate keepsake by default; optional OpenAI legacy.
        style_text = (photo.style or "").strip()
        try:
            if getattr(settings, "KEEPSAKE_USE_OPENAI_LEGACY", False):
                relative_path = generate_wedding_with_openai(
                    guest_path,
                    bride_path,
                    style_text,
                    event_id=photo.event_id,
                    event_type=getattr(photo.event, "event_type", "wedding"),
                    include_bride=include_bride,
                )
            else:
                ks = run_keepsake_pipeline(
                    Path(guest_path),
                    Path(bride_path) if bride_path else None,
                    event_id=photo.event_id,
                    event_type=getattr(photo.event, "event_type", "wedding"),
                    refine_prompt=style_text or None,
                    include_bride=include_bride,
                )
                relative_path = ks.final_relative_path
        except Exception as e:
            photo.status = Photo.STATUS_PENDING
            photo.save(update_fields=["status"])
            msg = str(e)
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            if "not configured" in msg or "not found" in msg:
                status_code = status.HTTP_400_BAD_REQUEST
            return Response(
                {"error": f"Image generation failed: {msg}"},
                status=status_code,
            )

        # 4. Save the generated image path into the model and mark completed.
        photo.generated_image = relative_path
        photo.status = Photo.STATUS_COMPLETED
        photo.save(update_fields=["generated_image", "status"])

        # 5. Return the URL so the client can show or download the image.
        url = request.build_absolute_uri(photo.generated_image.url)
        return Response({"generated_image_url": url, "status": photo.status})


# --- QR code & download flow: guest gets QR -> scans -> hits download URL -> gets image ---

# GET /api/photos/{id}/qr/
# Returns QR code image URL and download URL. Only for photos that have generated_image.
class PhotoQRCodeView(APIView):
    """
    Generate a QR code that points to the photo download URL.
    Flow: photo must have generated_image -> build download URL -> generate QR -> return both URLs.
    Kiosk can display the QR; guest scans it and is taken to the download endpoint.
    """

    def get(self, request, pk):
        photo = get_object_or_404(Photo, pk=pk)
        if not photo.generated_image:
            return Response(
                {"error": "Photo has no generated image yet. Run process-ai first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Build the full URL for the QR so phones on the same network can reach the backend.
        download_path = f"/api/photos/{pk}/download/"
        if getattr(settings, "PUBLIC_HOST", None):
            scheme = getattr(settings, "PUBLIC_SCHEME", "http")
            port = getattr(settings, "PUBLIC_PORT", "8000")
            port_suffix = f":{port}" if port and port not in ("80", "443") else ""
            download_url_absolute = f"{scheme}://{settings.PUBLIC_HOST}{port_suffix}{download_path}"
        else:
            download_url_absolute = request.build_absolute_uri(download_path)

        # Save QR under media/qrcodes/photo_{id}.png and get relative path.
        relative_path = generate_qr_code(
            download_url_absolute,
            filename=f"photo_{pk}.png",
            subdir=f"events/event_{photo.event_id}/qrcodes",
        )

        # Frontend uses download_url for "Or tap here" so it works on phones (full URL).
        qr_code_url = f"/media/{relative_path}"
        return Response({
            "qr_code_url": qr_code_url,
            "download_url": download_url_absolute,
        })


# GET /api/photos/{id}/download/
# Serves the generated image file so guests can download it (e.g. after scanning QR).
class PhotoDownloadView(APIView):
    """
    Serve the generated photo as a downloadable file.
    Used when the guest opens the download URL (from QR or direct link).
    """

    def get(self, request, pk):
        photo = get_object_or_404(Photo, pk=pk)
        if not photo.generated_image:
            return Response(
                {"error": "No generated image available for this photo."},
                status=status.HTTP_404_NOT_FOUND,
            )

        file_handle = photo.generated_image.open("rb")
        filename = photo.generated_image.name.split("/")[-1] or "wedding_photo.png"

        # Pick a content type based on the file extension so that phones/browsers
        # interpret and display the downloaded image correctly.
        ext = filename.lower().rsplit(".", 1)[-1]
        if ext == "png":
            content_type = "image/png"
        elif ext in ("jpg", "jpeg"):
            content_type = "image/jpeg"
        else:
            content_type = "image/png"

        response = FileResponse(file_handle, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
