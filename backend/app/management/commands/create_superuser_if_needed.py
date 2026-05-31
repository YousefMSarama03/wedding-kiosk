"""
Management command: create_superuser_if_needed

Creates a Django superuser if none exists. Designed to be run at startup
(e.g. from entrypoint.sh) so that a fresh Railway deployment always has
admin access without manual intervention.

Usage:
    python manage.py create_superuser_if_needed

Environment variables:
    DJANGO_ADMIN_PASSWORD  Password for the created superuser.
                           If unset, a random 20-character password is generated
                           and printed to stdout — capture it from the deploy logs.
    DJANGO_ADMIN_USERNAME  Username for the superuser (default: admin).
    DJANGO_ADMIN_EMAIL     Email for the superuser (default: admin@wedding-kiosk.local).

The command is idempotent: if a superuser already exists it exits silently.
"""

import os
import secrets
import string

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


def _generate_password(length: int = 20) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Command(BaseCommand):
    help = "Create a superuser if none exists (idempotent, safe to run on every deploy)."

    def handle(self, *args, **options):
        User = get_user_model()

        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write("Superuser already exists — skipping creation.")
            return

        username = os.getenv("DJANGO_ADMIN_USERNAME", "admin").strip() or "admin"
        email = (
            os.getenv("DJANGO_ADMIN_EMAIL", "admin@wedding-kiosk.local").strip()
            or "admin@wedding-kiosk.local"
        )
        password = os.getenv("DJANGO_ADMIN_PASSWORD", "").strip()
        generated = False

        if not password:
            password = _generate_password()
            generated = True

        User.objects.create_superuser(username=username, email=email, password=password)

        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Superuser created successfully."))
        self.stdout.write(self.style.SUCCESS(f"  Username : {username}"))
        self.stdout.write(self.style.SUCCESS(f"  Email    : {email}"))
        if generated:
            self.stdout.write(
                self.style.WARNING(
                    f"  Password : {password}  ← SAVE THIS — it will not be shown again"
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    "  Tip: set DJANGO_ADMIN_PASSWORD env var to use a fixed password."
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("  Password : (set via DJANGO_ADMIN_PASSWORD env var)"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
