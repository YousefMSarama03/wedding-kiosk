"""
Management command: ensure_superuser

Creates a Django superuser from environment variables if no superuser exists yet.
Safe to run on every deploy — it is a no-op when a superuser is already present.

Environment variables (all optional; sensible defaults provided for safety):
    DJANGO_SUPERUSER_USERNAME  – default: "admin"
    DJANGO_SUPERUSER_EMAIL     – default: "admin@example.com"
    DJANGO_SUPERUSER_PASSWORD  – default: (none; command skips creation if unset)

Usage:
    python manage.py ensure_superuser
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Create a superuser from environment variables if none exists. "
        "No-op when a superuser is already present."
    )

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin").strip()
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "").strip()

        if not password:
            self.stdout.write(
                self.style.WARNING(
                    "DJANGO_SUPERUSER_PASSWORD is not set — skipping superuser creation. "
                    "Set this variable in Railway to enable automatic admin account creation."
                )
            )
            return

        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.SUCCESS("Superuser already exists — no action taken.")
            )
            return

        if User.objects.filter(username=username).exists():
            # A non-superuser account with this name exists; promote it.
            user = User.objects.get(username=username)
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Promoted existing user '{username}' to superuser."
                )
            )
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(
            self.style.SUCCESS(
                f"Superuser '{username}' created successfully."
            )
        )
