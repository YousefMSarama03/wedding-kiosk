from django.db import models
from events.models import Event, event_folder_name


def _safe_basename(filename: str) -> str:
    return filename.split("/")[-1].split("\\")[-1]


def _event_bucket(instance) -> str:
    event = getattr(instance, "event", None)
    if event is None:
        event_id = getattr(instance, "event_id", None)
        if event_id is not None:
            event = Event.objects.filter(pk=event_id).only(
                "bride_name", "groom_name", "wedding_date"
            ).first()
    if event is None:
        return "event_unknown"
    return event_folder_name(event)


def photo_guest_upload_to(instance, filename):
    return f"events/{_event_bucket(instance)}/guests/{_safe_basename(filename)}"


def photo_generated_upload_to(instance, filename):
    return f"events/{_event_bucket(instance)}/generated/{_safe_basename(filename)}"


class Photo(models.Model):
    """Guest photo linked to a wedding event, with optional AI-generated result."""

    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="photos")
    guest_image = models.ImageField(upload_to=photo_guest_upload_to)
    generated_image = models.ImageField(upload_to=photo_generated_upload_to, null=True, blank=True)
    style = models.CharField(max_length=100, blank=True)
    use_ai_generation = models.BooleanField(
        default=True,
        help_text="If False, guest capture is copied to generated/ (no AI).",
    )
    captured_by = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name of the person operating the camera.",
    )
    subject_names = models.CharField(
        max_length=250,
        blank=True,
        help_text="Comma-separated names of people in the image (e.g. guest, bride).",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    is_approved = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Photo #{self.id} ({self.event}) - {self.status}"
