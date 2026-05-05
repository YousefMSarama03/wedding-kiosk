from django.db import models
from django.utils.text import slugify


def event_bride_upload_to(instance, filename):
    """
    Organize bride/reference images under a per-event folder for easier lookup.
    """
    safe_filename = filename.split("/")[-1].split("\\")[-1]
    bride = slugify(getattr(instance, "bride_name", "") or "bride")
    groom = slugify(getattr(instance, "groom_name", "") or "groom")
    date_part = str(getattr(instance, "wedding_date", "") or "date")
    event_key = f"{bride}_{groom}_{date_part}"
    return f"events/{event_key}/bride/{safe_filename}"


class Event(models.Model):
    """A wedding event with bride, groom, date, and optional bride image."""

    EVENT_TYPE_WEDDING = "wedding"
    EVENT_TYPE_HENNA = "palestinian_henna"
    EVENT_TYPE_GRADUATION = "graduation"
    EVENT_TYPE_CHOICES = [
        (EVENT_TYPE_WEDDING, "Wedding"),
        (EVENT_TYPE_HENNA, "Palestinian Henna Party"),
        (EVENT_TYPE_GRADUATION, "Graduation"),
    ]

    bride_name = models.CharField(max_length=255)
    groom_name = models.CharField(max_length=255)
    event_type = models.CharField(
        max_length=32,
        choices=EVENT_TYPE_CHOICES,
        default=EVENT_TYPE_WEDDING,
    )
    wedding_date = models.DateField()
    bride_image = models.ImageField(upload_to=event_bride_upload_to, blank=True, null=True)
    max_photos = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of guest photos for this event; leave empty for no limit.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.bride_name} & {self.groom_name} ({self.wedding_date})"

    def at_photo_limit(self) -> bool:
        if self.max_photos is None:
            return False
        return self.photos.count() >= self.max_photos


class Bride(models.Model):
    """
    Global bride image used for AI generation.
    The admin uploads this once and marks it active; the AI pipeline uses
    Bride.image (wedding photo) and places the guest into it as a keepsake.
    """
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to="bride/")
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.active:
            Bride.objects.exclude(pk=self.pk).filter(active=True).update(active=False)

    def __str__(self):
        return f"Bride {self.name} ({'active' if self.active else 'inactive'})"
