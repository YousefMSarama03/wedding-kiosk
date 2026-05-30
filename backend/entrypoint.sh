#!/bin/sh
set -e

# Default PORT if not provided by environment (Railway sets $PORT)
: "${PORT:=8000}"

# Preflight: ensure a database config is present in production
if [ "${DEBUG:-false}" != "true" ]; then
	if [ -z "${DATABASE_URL}" ] && [ -z "${POSTGRES_HOST}" ]; then
		echo "ERROR: No DATABASE_URL or POSTGRES_HOST set and DEBUG!=true. Set DATABASE_URL for production." >&2
		exit 1
	fi
fi

echo "Waiting for DB (if needed) and running migrations..."
RETRIES=10
DELAY=3
count=0
until python manage.py migrate --noinput; do
	count=$((count+1))
	if [ "$count" -ge "$RETRIES" ]; then
		echo "migrate failed after $RETRIES attempts" >&2
		exit 1
	fi
	echo "migrate failed, retrying in $DELAY seconds... (attempt $count/$RETRIES)"
	sleep $DELAY
done

echo "Creating superuser if none exists..."
python manage.py ensure_superuser

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting gunicorn on 0.0.0.0:${PORT}"
# Use exec so signals are forwarded to Gunicorn
exec gunicorn app.wsgi:application --bind "0.0.0.0:${PORT}" --workers "${WEB_CONCURRENCY:-2}" --log-level "${GUNICORN_LOG_LEVEL:-info}" --timeout "${GUNICORN_TIMEOUT:-30}"
