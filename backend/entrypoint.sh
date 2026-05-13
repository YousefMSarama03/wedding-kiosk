#!/bin/bash
# Django backend entrypoint for Railway
# Handles migrations and static file collection before starting Gunicorn

set -e

echo "======================================"
echo "Django Backend Startup"
echo "======================================"
echo "DEBUG: ${DEBUG:-false}"
echo "PORT: ${PORT:-8000}"
echo "ALLOWED_HOSTS: ${ALLOWED_HOSTS:-localhost,127.0.0.1}"
echo ""

# Wait for database to be ready (Railway PostgreSQL)
echo "Checking database connection..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if python -c "
import os
import dj_database_url
import psycopg
try:
    if os.getenv('DATABASE_URL'):
        db_config = dj_database_url.config()
    else:
        db_config = {
            'dbname': os.getenv('POSTGRES_DB', 'wedding_kiosk'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
        }
    conn = psycopg.connect(**db_config, timeout=5)
    conn.close()
    print('Database is ready!')
    exit(0)
except Exception as e:
    print(f'Database not ready: {e}')
    exit(1)
" 2>&1; then
        echo "✓ Database is ready!"
        break
    fi
    attempt=$((attempt + 1))
    if [ $attempt -lt $max_attempts ]; then
        echo "  Retrying... ($attempt/$max_attempts)"
        sleep 1
    fi
done

if [ $attempt -ge $max_attempts ]; then
    echo "✗ Database connection failed after $max_attempts attempts"
    # Don't exit - Railway might have healthcheck configured
fi

echo ""
echo "Running migrations..."
python manage.py migrate --noinput 2>&1 || {
    echo "⚠ Migration warning (may already be applied)"
}

echo ""
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear 2>&1 || {
    echo "⚠ Static files collection warning"
}

echo ""
echo "======================================"
echo "Starting application server..."
echo "======================================"
echo ""

# Start the app based on DEBUG mode
if [ "$DEBUG" = "true" ]; then
    echo "Starting Django development server (runserver)..."
    exec python manage.py runserver 0.0.0.0:${PORT:-8000}
else
    echo "Starting Gunicorn production server..."
    exec gunicorn \
        app.wsgi:application \
        --bind 0.0.0.0:${PORT:-8000} \
        --workers 4 \
        --worker-class sync \
        --timeout 120 \
        --access-logfile - \
        --error-logfile - \
        --max-requests 1000 \
        --max-requests-jitter 50
fi
