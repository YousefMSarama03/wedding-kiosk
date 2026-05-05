from django.contrib import admin
from .models import Photo


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "status", "style", "created_at")
    list_filter = ("status", "event")
    search_fields = ("event__bride_name", "event__groom_name")
    raw_id_fields = ("event",)
