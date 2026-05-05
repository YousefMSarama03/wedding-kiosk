"""
Serializers for the photos app.
Expose Photo model as JSON for list and create.
"""

from rest_framework import serializers
from .models import Photo


class PhotoSerializer(serializers.ModelSerializer):
    """
    Serializes a Photo. Used for GET (list/detail) and POST (create).
    On create, send 'event' (id), 'guest_image' (file), and optionally 'style'.
    status defaults to 'pending' on the model.
    """
    class Meta:
        model = Photo
        fields = [
            "id",
            "event",
            "guest_image",
            "generated_image",
            "style",
            "captured_by",
            "subject_names",
            "status",
            "is_approved",
            "is_featured",
            "is_hidden",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "generated_image",
            "status",
            "created_at",
            "is_approved",
            "is_featured",
            "is_hidden",
        ]
