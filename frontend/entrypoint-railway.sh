#!/bin/sh
set -e
if [ -z "${BACKEND_PROXY_URL}" ]; then
  echo "BACKEND_PROXY_URL is required (public URL of your Django service, e.g. https://backend-production-xxxx.up.railway.app)" >&2
  exit 1
fi
export PORT="${PORT:-8080}"
case "${BACKEND_PROXY_URL}" in
  */) export BACKEND_PROXY_URL ;;
  *) export BACKEND_PROXY_URL="${BACKEND_PROXY_URL}/" ;;
esac
envsubst '${PORT} ${BACKEND_PROXY_URL}' < /etc/nginx/nginx.railway.template > /etc/nginx/conf.d/default.conf
exec nginx -g "daemon off;"
