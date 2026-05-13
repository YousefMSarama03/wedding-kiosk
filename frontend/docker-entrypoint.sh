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

# Add health check endpoint to nginx config
cat >> /etc/nginx/conf.d/default.conf << 'EOF'

# Health check endpoint for Railway
location /health {
    access_log off;
    return 200 "OK";
    add_header Content-Type text/plain;
}

# DNS resolver for Railway
resolver 127.0.0.11 8.8.8.8 valid=10s;
resolver_timeout 5s;
EOF

# Validate nginx config
nginx -t

echo "Starting nginx..."
exec nginx -g 'daemon off;'
