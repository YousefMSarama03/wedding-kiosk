#!/bin/sh
set -e

# Resolve PORT with a fallback to 8000
export PORT="${PORT:-8000}"

echo "Starting gunicorn on port $PORT"

exec gunicorn app.wsgi:application --bind "0.0.0.0:${PORT}"
