"""
Serializers for the events app.
Expose Event model as JSON; include nested photos when an event is retrieved.
"""

from rest_framework import serializers
from .models import Event

# Import here to nest photos inside event responses (no circular import:
# photos.serializers does not import from events.serializers).
from photos.serializers import PhotoSerializer


class NullablePositiveIntField(serializers.IntegerField):
    """Multipart forms send '' for empty; treat as unlimited (null)."""

    def __init__(self, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("allow_null", True)
        kwargs.setdefault("min_value", 1)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if data in (None, ""):
            return None
        return super().to_internal_value(data)


class EventSerializer(serializers.ModelSerializer):
    """
    Serializes an Event. When reading (GET), includes its related photos.
    When writing (POST), only event fields are required; photos are read-only.
    """
    # Nested list of photos for this event (read-only; not used on create/update).
    photos = PhotoSerializer(many=True, read_only=True)
    max_photos = NullablePositiveIntField()

    class Meta:
        model = Event
        fields = [
            "id",
            "bride_name",
            "groom_name",
            "event_type",
            "wedding_date",
            "bride_image",
            "max_photos",
            "created_at",
            "photos",
        ]
        read_only_fields = ["id", "created_at"]
