# Railway Environment Variables Reference

Complete reference for all environment variables required (or recommended) for a
production deployment on Railway. Set these in the **Variables** tab of each service.

---

## Backend Service

### Required

| Variable | Example / Notes |
|---|---|
| `DATABASE_URL` | Set via Railway PostgreSQL reference variable: `${{Postgres.DATABASE_URL}}` |
| `DJANGO_SECRET_KEY` | Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `ALLOWED_HOSTS` | Comma-separated: `backend-production-xxxx.up.railway.app` |

### Admin Access

| Variable | Default | Notes |
|---|---|---|
| `DJANGO_SUPERUSER_USERNAME` | `admin` | Username for the auto-created admin account |
| `DJANGO_SUPERUSER_EMAIL` | `admin@example.com` | Email for the auto-created admin account |
| `DJANGO_SUPERUSER_PASSWORD` | *(none — creation skipped if unset)* | **Set this** to enable automatic superuser creation on first deploy |

> The `ensure_superuser` management command runs on every deploy (via `entrypoint.sh`).
> It is a no-op once a superuser already exists, so it is safe to leave set permanently.
> Admin panel: `https://backend-production-xxxx.up.railway.app/admin/`

### Security

| Variable | Recommended Value | Notes |
|---|---|---|
| `DEBUG` | `false` | Never `true` in production |
| `SECURE_SSL_REDIRECT` | `true` | Redirect HTTP → HTTPS (Railway proxy handles TLS) |
| `SESSION_COOKIE_SECURE` | `true` | Cookies only sent over HTTPS |
| `CSRF_COOKIE_SECURE` | `true` | CSRF cookie only sent over HTTPS |
| `SECURE_HSTS_SECONDS` | `31536000` | 1-year HSTS (set to `0` to disable during initial rollout) |

### CORS / CSRF

| Variable | Example | Notes |
|---|---|---|
| `CORS_ALLOWED_ORIGINS` | `https://frontend-production-xxxx.up.railway.app` | Exact frontend origin; leave empty to allow all `*.up.railway.app` via regex |
| `CSRF_TRUSTED_ORIGINS` | `https://frontend-production-xxxx.up.railway.app` | Must include the frontend origin for cross-origin POST/PATCH/DELETE |

### Public URL (QR codes)

| Variable | Example | Notes |
|---|---|---|
| `PUBLIC_HOST` | `backend-production-xxxx.up.railway.app` | Hostname used in QR download links |
| `PUBLIC_SCHEME` | `https` | Protocol for QR links |
| `PUBLIC_PORT` | *(leave empty)* | Leave empty for default 443; Railway handles port mapping |
| `API_PUBLIC_BASE_URL` | `https://backend-production-xxxx.up.railway.app` | Full base URL for QR/download links when `request` is unavailable (e.g. Celery tasks) |

### Cloudinary (Media Storage)

| Variable | Notes |
|---|---|
| `CLOUDINARY_CLOUD_NAME` | From Cloudinary dashboard → Settings → API Keys |
| `CLOUDINARY_API_KEY` | From Cloudinary dashboard |
| `CLOUDINARY_API_SECRET` | From Cloudinary dashboard |

### AI / Generation

| Variable | Notes |
|---|---|
| `REPLICATE_API_TOKEN` | Required for default keepsake generation (InstantID on Replicate) |
| `REPLICATE_MODEL` | Optional; full model ID e.g. `black-forest-labs/flux-2-pro` |
| `REPLICATE_INSTANTID_MODEL` | Legacy env name; used if `REPLICATE_MODEL` is empty |
| `OPENAI_API_KEY` | Only needed if `KEEPSAKE_USE_OPENAI_LEGACY=true` |
| `KEEPSAKE_USE_OPENAI_LEGACY` | `true` to use DALL-E instead of Replicate |
| `OPENAI_IMAGE_MODEL` | Default: `dall-e-2` |

### Celery / Redis (optional)

| Variable | Notes |
|---|---|
| `REDIS_URL` | Railway Redis reference: `${{Redis.REDIS_URL}}` |
| `CELERY_BROKER_URL` | Overrides `REDIS_URL` for the broker if different |
| `CELERY_RESULT_BACKEND` | Overrides `REDIS_URL` for results if different |
| `CELERY_TASK_TIME_LIMIT` | Default: `900` (seconds) |
| `CELERY_TASK_SOFT_TIME_LIMIT` | Default: `840` (seconds) |

### Gunicorn Tuning

| Variable | Default | Notes |
|---|---|---|
| `PORT` | Set by Railway automatically | Do not override |
| `WEB_CONCURRENCY` | `2` | Number of Gunicorn worker processes |
| `GUNICORN_LOG_LEVEL` | `info` | `debug`, `info`, `warning`, `error`, `critical` |
| `GUNICORN_TIMEOUT` | `30` | Worker timeout in seconds; increase for slow AI requests |

---

## Frontend Service

### Required

| Variable | Example | Notes |
|---|---|---|
| `VITE_API_URL` | `https://backend-production-xxxx.up.railway.app` | **Build-time** variable — must be set before the Docker image is built. Points the React app at the Django backend. |
| `BACKEND_URL` | `https://backend-production-xxxx.up.railway.app` | **Runtime** variable — used by nginx to proxy `/api/` and `/media/` requests to the backend. |

> **Important:** `VITE_API_URL` is baked into the compiled JavaScript bundle at build time.
> If you change the backend URL, you must trigger a new frontend deploy/build for the change to take effect.

---

## Quick Setup Checklist

1. **PostgreSQL**: Add a Railway PostgreSQL plugin and reference `${{Postgres.DATABASE_URL}}` in the backend `DATABASE_URL` variable.
2. **Backend variables**: Set `DJANGO_SECRET_KEY`, `ALLOWED_HOSTS`, `DJANGO_SUPERUSER_PASSWORD`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `PUBLIC_HOST`, `PUBLIC_SCHEME`, and `CLOUDINARY_*`.
3. **Frontend variables**: Set `VITE_API_URL` and `BACKEND_URL` to the backend Railway domain.
4. **Deploy backend first** — migrations and superuser creation run automatically on startup.
5. **Access admin** at `https://<backend-domain>/admin/` with the credentials from `DJANGO_SUPERUSER_USERNAME` / `DJANGO_SUPERUSER_PASSWORD`.
