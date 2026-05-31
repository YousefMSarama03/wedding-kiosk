"""
Create a Django superuser if none exists.

Usage:
    python manage.py create_superuser_if_needed

Reads DJANGO_ADMIN_PASSWORD from the environment; if unset, generates a
random 20-character password and prints it to stdout so it appears in
Railway deploy logs.

Safe to run multiple times — it is a no-op when a superuser already exists.
"""

import os
import secrets
import string

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a superuser if none exists (idempotent)."

    def handle(self, *args, **options):
        User = get_user_model()

        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write("Superuser already exists — skipping creation.")
            return

        username = "admin"
        email = "admin@wedding-kiosk.local"
        password = os.environ.get("DJANGO_ADMIN_PASSWORD", "").strip()

        if not password:
            alphabet = string.ascii_letters + string.digits
            password = "".join(secrets.choice(alphabet) for _ in range(20))
            self.stdout.write(
                self.style.WARNING(
                    f"DJANGO_ADMIN_PASSWORD not set — generated random password."
                )
            )

        User.objects.create_superuser(username=username, email=email, password=password)

        self.stdout.write(
            self.style.SUCCESS(
                f"Superuser created.\n"
                f"  Username : {username}\n"
                f"  Email    : {email}\n"
                f"  Password : {password}"
            )
        )
