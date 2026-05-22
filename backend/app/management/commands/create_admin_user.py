"""
Create a Django superuser for the admin panel.

Checks whether the user already exists before creating, so it is safe
to run repeatedly (e.g. as part of a deploy script).

Usage:
    # Use built-in defaults (username: yousef, password: 123456789)
    python manage.py create_admin_user

    # Supply custom credentials
    python manage.py create_admin_user <username> <password>

    # Explicit flags
    python manage.py create_admin_user --username yousef --password 123456789
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a superuser for the Django admin panel if one does not already exist."

    def add_arguments(self, parser):
        parser.add_argument(
            "username",
            nargs="?",
            default="yousef",
            help="Username for the admin account (default: yousef).",
        )
        parser.add_argument(
            "password",
            nargs="?",
            default="123456789",
            help="Password for the admin account (default: 123456789).",
        )
        parser.add_argument(
            "--username",
            dest="username_flag",
            default=None,
            help="Username (alternative to positional argument).",
        )
        parser.add_argument(
            "--password",
            dest="password_flag",
            default=None,
            help="Password (alternative to positional argument).",
        )

    def handle(self, *args, **options):
        User = get_user_model()

        # Explicit flags take precedence over positional arguments.
        username = options["username_flag"] or options["username"]
        password = options["password_flag"] or options["password"]

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"Admin user '{username}' already exists. No changes made."
                )
            )
            return

        User.objects.create_superuser(username=username, password=password)
        self.stdout.write(
            self.style.SUCCESS(
                f"Superuser '{username}' created successfully."
            )
        )
