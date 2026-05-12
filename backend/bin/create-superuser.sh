#!/bin/sh
# Creates a Django superuser non-interactively using environment variables.
# Safe to run multiple times — skips creation if the user already exists.
#
# Required environment variables:
#   SUPERUSER_USERNAME  – the admin username
#   SUPERUSER_EMAIL     – the admin email address
#   SUPERUSER_PASSWORD  – the admin password
#
# Usage (Railway one-off command or local):
#   SUPERUSER_USERNAME=admin \
#   SUPERUSER_EMAIL=admin@example.com \
#   SUPERUSER_PASSWORD=secret \
#   ./bin/create-superuser.sh

set -e

: "${SUPERUSER_USERNAME:?SUPERUSER_USERNAME environment variable is required}"
: "${SUPERUSER_EMAIL:?SUPERUSER_EMAIL environment variable is required}"
: "${SUPERUSER_PASSWORD:?SUPERUSER_PASSWORD environment variable is required}"

echo "Creating superuser '${SUPERUSER_USERNAME}'..."

python manage.py shell <<EOF
from django.contrib.auth import get_user_model

User = get_user_model()

if User.objects.filter(username="${SUPERUSER_USERNAME}").exists():
    print("Superuser '${SUPERUSER_USERNAME}' already exists — skipping creation.")
else:
    User.objects.create_superuser(
        username="${SUPERUSER_USERNAME}",
        email="${SUPERUSER_EMAIL}",
        password="${SUPERUSER_PASSWORD}",
    )
    print("Superuser '${SUPERUSER_USERNAME}' created successfully.")
EOF
