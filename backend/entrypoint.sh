#!/bin/sh
set -e

echo "Running Django migrations..."
python manage.py migrate --noinput

echo "Starting Gunicorn..."
exec gunicorn app.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers 2 \
    --timeout 120
