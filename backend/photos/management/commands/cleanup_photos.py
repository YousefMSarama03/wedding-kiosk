"""
Delete Photo objects older than 3 days and their files from MEDIA_ROOT.

Usage:
    python manage.py cleanup_photos

Safe to run repeatedly; missing files are skipped.
"""

import os

from django.core.management.base import BaseCommand
from django.utils.timezone import now
from datetime import timedelta

from photos.models import Photo


def safe_delete_file(file_field):
    """Delete the file from disk if it exists. No-op if file is empty or missing."""
    if not file_field:
        return False
    try:
        path = file_field.path
        if path and os.path.isfile(path):
            os.remove(path)
            return True
    except (ValueError, OSError):
        pass
    return False


class Command(BaseCommand):
    help = "Delete photos older than 3 days and their guest_image / generated_image files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=3,
            help="Delete photos older than this many days (default: 3).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only report what would be deleted; do not delete.",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]
        threshold = now() - timedelta(days=days)

        qs = Photo.objects.filter(created_at__lt=threshold)
        to_delete = list(qs)
        count = len(to_delete)

        if count == 0:
            self.stdout.write(self.style.SUCCESS(f"No photos older than {days} days."))
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"Would delete {count} photo(s) (--dry-run).")
            )
            return

        files_removed = 0
        for photo in to_delete:
            if photo.guest_image:
                if safe_delete_file(photo.guest_image):
                    files_removed += 1
            if photo.generated_image:
                if safe_delete_file(photo.generated_image):
                    files_removed += 1
            photo.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Removed {count} photo(s) and {files_removed} file(s) from disk."
            )
        )
