from django.contrib import admin
from .models import Event, Bride


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("bride_name", "groom_name", "event_type", "wedding_date", "has_bride_image", "created_at")
    list_filter = ("event_type", "wedding_date",)
    search_fields = ("bride_name", "groom_name")
    date_hierarchy = "wedding_date"

    fieldsets = (
        (
            None,
            {
                "fields": ("bride_name", "groom_name", "event_type", "wedding_date", "max_photos"),
                "description": "Max photos: leave blank for unlimited guest captures.",
            },
        ),
        (
            "Bride photo (required for AI)",
            {
                "fields": ("bride_image",),
                "description": "Upload a photo of the bride. Required for AI wedding photo generation. "
                "Guests’ photos are combined with this in the AI scene.",
            },
        ),
    )

    @admin.display(boolean=True, description="Bride photo")
    def has_bride_image(self, obj):
        return bool(obj.bride_image)


@admin.register(Bride)
class BrideAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "created_at")
    list_filter = ("active",)
    search_fields = ("name",)
    readonly_fields = ("created_at",)
