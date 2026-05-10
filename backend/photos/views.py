"""
API views for photos.
Uses DRF generic views: list/create and a custom view for AI processing.
"""

import base64
import uuid

from django.core.files.base import ContentFile
from django.db import transaction
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
from celery import chain
from events.models import Event
from .models import Photo
from .serializers import PhotoSerializer
from .services.photo_qr import build_photo_download_absolute_url, materialize_photo_qr
from .tasks import materialize_photo_qr_task, process_photo_ai_task


def _parse_use_ai_from_request(value) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ("false", "0", "no", "off"):
        return False
    return True


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
    Request body: event_id, style (optional), use_ai (optional, default true), image_base64.
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
        use_ai = _parse_use_ai_from_request(request.data.get("use_ai"))
        use_ai_generation = True if use_ai is None else use_ai

        photo = Photo.objects.create(
            event=event,
            guest_image=content,
            style=style,
            use_ai_generation=use_ai_generation,
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
@method_decorator(csrf_exempt, name="dispatch")
class PhotoProcessAIView(APIView):
    """
    Queue or run AI processing. With ``CELERY_BROKER_URL`` set, returns 202 quickly and runs
    ``process_photo_ai_task`` → ``materialize_photo_qr_task`` in the background.

    QR and download URL do not require a finished image: GET /qr/ works immediately;
    GET /download/ returns JSON ``{ "status": "processing" }`` until the file exists.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, pk):
        style = request.data.get("style")
        use_ai_override = _parse_use_ai_from_request(request.data.get("use_ai"))
        guest_only_finalize_after = False
        photo_id: int | None = None

        with transaction.atomic():
            photo = get_object_or_404(Photo.objects.select_for_update(), pk=pk)
            update_fields: list[str] = []
            if style is not None:
                photo.style = style
                update_fields.append("style")
            if use_ai_override is not None:
                photo.use_ai_generation = use_ai_override
                update_fields.append("use_ai_generation")

            if (
                photo.status == Photo.STATUS_COMPLETED
                and photo.generated_image
                and photo.generated_image.name
            ):
                if update_fields:
                    photo.save(update_fields=update_fields)
                url = request.build_absolute_uri(photo.generated_image.url)
                return Response(
                    {
                        "generated_image_url": url,
                        "status": photo.status,
                        "guest_only": not photo.use_ai_generation,
                        "idempotent": True,
                    },
                    status=status.HTTP_200_OK,
                )

            if photo.status == Photo.STATUS_PROCESSING and photo.use_ai_generation:
                if update_fields:
                    photo.save(update_fields=update_fields)
                detail_url = request.build_absolute_uri(f"/api/photos/{photo.pk}/")
                return Response(
                    {
                        "status": photo.status,
                        "photo_id": photo.pk,
                        "detail_url": detail_url,
                        "message": "Already processing; poll detail_url until status is completed.",
                    },
                    status=status.HTTP_202_ACCEPTED,
                )

            if not photo.use_ai_generation:
                uf = list(dict.fromkeys(update_fields))
                if uf:
                    photo.save(update_fields=uf)
                photo_id = photo.pk
                guest_only_finalize_after = True
            else:
                photo.status = Photo.STATUS_PROCESSING
                update_fields.append("status")
                photo.save(update_fields=update_fields)
                photo_id = photo.pk

        if guest_only_finalize_after and photo_id is not None:
            from .services.photo_ai_job import finalize_photo_guest_only

            finalize_photo_guest_only(photo_id)
            materialize_photo_qr(photo_id, request=request)
            photo = Photo.objects.get(pk=photo_id)
            url = request.build_absolute_uri(photo.generated_image.url)
            return Response(
                {
                    "status": photo.status,
                    "guest_only": True,
                    "generated_image_url": url,
                    "image_url": url,
                },
                status=status.HTTP_200_OK,
            )

        use_celery = bool(getattr(settings, "CELERY_BROKER_URL", "").strip())

        if use_celery:
            chain(
                process_photo_ai_task.s(photo_id),
                materialize_photo_qr_task.s(),
            ).delay()
            photo.refresh_from_db()
            if photo.status == Photo.STATUS_COMPLETED and photo.generated_image:
                url = request.build_absolute_uri(photo.generated_image.url)
                return Response(
                    {"generated_image_url": url, "status": photo.status},
                    status=status.HTTP_200_OK,
                )
            detail_url = request.build_absolute_uri(f"/api/photos/{photo_id}/")
            return Response(
                {
                    "status": photo.status,
                    "photo_id": photo_id,
                    "detail_url": detail_url,
                    "message": "Processing started; poll detail_url until status is completed.",
                },
                status=status.HTTP_202_ACCEPTED,
            )

        try:
            execute_sync_ai_and_qr(photo_id)
        except Exception as e:
            Photo.objects.filter(pk=photo_id).update(status=Photo.STATUS_PENDING)
            msg = str(e)
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            if "not configured" in msg or "not found" in msg:
                status_code = status.HTTP_400_BAD_REQUEST
            return Response(
                {"error": f"Image generation failed: {msg}"},
                status=status_code,
            )

        photo.refresh_from_db()
        url = request.build_absolute_uri(photo.generated_image.url)
        return Response({"generated_image_url": url, "status": photo.status})


def execute_sync_ai_and_qr(photo_id: int) -> None:
    """Run AI pipeline or guest-only copy, then write QR."""
    from .services.photo_ai_job import execute_photo_ai_processing, finalize_photo_guest_only

    photo = Photo.objects.get(pk=photo_id)
    if not photo.use_ai_generation:
        finalize_photo_guest_only(photo_id)
    else:
        execute_photo_ai_processing(photo_id)
    materialize_photo_qr(photo_id, request=None)


# --- QR code & download flow: guest gets QR -> scans -> hits download URL -> gets image ---

# GET /api/photos/{id}/qr/
class PhotoQRCodeView(APIView):
    """
    Return QR for the stable download URL. Does not require ``generated_image``;
    the guest may scan before AI finishes.
    """

    def get(self, request, pk):
        photo = get_object_or_404(Photo, pk=pk)
        download_url_absolute = build_photo_download_absolute_url(pk, request=request)
        relative_path = materialize_photo_qr(pk, request=request)
        qr_code_url = f"/media/{relative_path}"
        return Response({
            "qr_code_url": qr_code_url,
            "download_url": download_url_absolute,
            "photo_status": photo.status,
            "guest_only": not photo.use_ai_generation,
        })


# GET /api/photos/{id}/download/
class PhotoDownloadView(APIView):
    """
    Serve the generated file when ready; otherwise JSON ``status: processing`` (HTTP 200).
    """

    def get(self, request, pk):
        photo = get_object_or_404(Photo, pk=pk)
        has_file = bool(photo.generated_image and photo.generated_image.name)
        if photo.status == Photo.STATUS_COMPLETED and has_file:
            file_handle = photo.generated_image.open("rb")
            filename = photo.generated_image.name.split("/")[-1] or "wedding_photo.png"
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

        if (
            photo.status == Photo.STATUS_COMPLETED
            and not photo.use_ai_generation
            and photo.guest_image
            and photo.guest_image.name
        ):
            file_handle = photo.guest_image.open("rb")
            filename = photo.guest_image.name.split("/")[-1] or "photo.jpg"
            ext = filename.lower().rsplit(".", 1)[-1]
            if ext in ("jpg", "jpeg"):
                content_type = "image/jpeg"
            elif ext == "png":
                content_type = "image/png"
            else:
                content_type = "image/jpeg"
            response = FileResponse(file_handle, content_type=content_type)
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response

        return Response(
            {
                "status": "processing",
                "photo_status": photo.status,
                "message": "Your photo is still being generated. Try again in a moment.",
            },
            status=status.HTTP_200_OK,
        )
