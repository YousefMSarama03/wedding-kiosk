#!/bin/sh
set -e

# Resolve PORT: use Railway's $PORT if set, otherwise default to 8000
PORT="${PORT:-8000}"
export PORT

echo "Starting backend on port $PORT"

# Run database migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Start gunicorn in the foreground
echo "Starting gunicorn bound to 0.0.0.0:$PORT"
exec gunicorn app.wsgi:application --bind "0.0.0.0:$PORT"
