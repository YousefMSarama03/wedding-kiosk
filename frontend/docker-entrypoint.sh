#!/bin/sh
set -e

# Default values
: "${PORT:=80}"
: "${BACKEND_URL:=https://wedding-kiosk-backend-production.up.railway.app}"

echo "Frontend starting..."
echo "  PORT: $PORT"
echo "  BACKEND_URL: $BACKEND_URL"

# Replace environment variables in nginx config
envsubst '${PORT} ${BACKEND_URL}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# Validate nginx config
nginx -t

echo "Starting nginx..."
exec nginx -g 'daemon off;'
