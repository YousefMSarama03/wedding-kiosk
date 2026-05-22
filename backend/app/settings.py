"""
Django settings for app project.
"""

import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import logging

from dotenv import load_dotenv


def bool_env(name, default="false"):
    return os.getenv(name, default).strip().lower() in ("true", "1", "yes")


def split_env_list(name, default=""):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def parse_database_url(url):
    parsed = urlparse(url)
    options = {}
    query = parse_qs(parsed.query)
    if query.get("sslmode"):
        options["sslmode"] = query.get("sslmode", [""])[0]
    if query.get("sslrootcert"):
        options["sslrootcert"] = query.get("sslrootcert", [""])[0]
    if query.get("sslcert"):
        options["sslcert"] = query.get("sslcert", [""])[0]
    if query.get("sslkey"):
        options["sslkey"] = query.get("sslkey", [""])[0]

    db_settings = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": parsed.path.lstrip("/") if parsed.path else "",
        "USER": parsed.username or "",
        "PASSWORD": parsed.password or "",
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or ""),
    }
    if options:
        db_settings["OPTIONS"] = options
    return db_settings


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "change-this-secret-key-in-production-8eR5DpLAkzBv1HtNq7mUfGjZ0CxQy2W",
)

DEBUG = bool_env("DEBUG", "false")

ALLOWED_HOSTS = split_env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
# If set, QR download URLs use this host so phones on the same network can reach the backend.
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "").strip()
PUBLIC_SCHEME = os.getenv("PUBLIC_SCHEME", "http").strip() or "http"
PUBLIC_PORT = os.getenv("PUBLIC_PORT", "8000").strip()
if PUBLIC_HOST and PUBLIC_HOST not in ALLOWED_HOSTS:
    ALLOWED_HOSTS = list(ALLOWED_HOSTS) + [PUBLIC_HOST]

# Conservative fallback: if ALLOWED_HOSTS came out empty, ensure the known Railway host
# is present so Django doesn't return DisallowedHost (which prevents CORS headers).
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["backend-production-535b.up.railway.app"]

# Log resolved ALLOWED_HOSTS for easier debugging on startup. Use logging and print
# so it's visible across different deployment log collectors.
try:
    logging.getLogger(__name__).info(f"Resolved ALLOWED_HOSTS: {ALLOWED_HOSTS}")
except Exception:
    pass
print(f"Resolved ALLOWED_HOSTS: {ALLOWED_HOSTS}")

# Production security for Railway environment.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = bool_env("SECURE_SSL_REDIRECT", "true") if not DEBUG else False
SESSION_COOKIE_SECURE = bool_env("SESSION_COOKIE_SECURE", "true")
CSRF_COOKIE_SECURE = bool_env("CSRF_COOKIE_SECURE", "true")
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0")) if DEBUG else int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = bool_env("SECURE_HSTS_INCLUDE_SUBDOMAINS", "true")
SECURE_HSTS_PRELOAD = bool_env("SECURE_HSTS_PRELOAD", "true")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "events",
    "photos",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "app.wsgi.application"

if os.getenv("DATABASE_URL"):
    DATABASES = {
        "default": parse_database_url(os.getenv("DATABASE_URL"))
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "wedding_kiosk"),
            "USER": os.getenv("POSTGRES_USER", "postgres"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "postgres"),
            # Default "localhost" for running Django on the host; Docker Compose sets POSTGRES_HOST=db in the backend container.
            "HOST": os.getenv("POSTGRES_HOST", "localhost"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = split_env_list(
    "CORS_ALLOWED_ORIGINS",
    "https://frontend-production-e4dc9.up.railway.app,http://localhost:3000,http://127.0.0.1:3000",
)
# Required for session auth when frontend and backend are on different origins (e.g. production).
CORS_ALLOW_CREDENTIALS = True

# If the environment variable was set but empty (or split_env_list produced an empty list),
# provide a safe fallback so preflight requests still receive CORS headers in production.
if not CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS = [
        "https://frontend-production-e4dc9.up.railway.app",
    ]

# Log resolved CORS origins for easier debugging on startup.
# Use both logging and print so it's visible in different deployment logs.
logger = logging.getLogger(__name__)
try:
    logger.info(f"Resolved CORS_ALLOWED_ORIGINS: {CORS_ALLOWED_ORIGINS}")
except Exception:
    # Ensure settings import never raises because of logging issues.
    pass
print(f"Resolved CORS_ALLOWED_ORIGINS: {CORS_ALLOWED_ORIGINS}")

# Required in Django 4+ when frontend sends requests to the API.
CSRF_TRUSTED_ORIGINS = split_env_list(
    "CSRF_TRUSTED_ORIGINS",
    "https://frontend-production-e4dc9.up.railway.app,http://localhost:3000,http://127.0.0.1:3000",
)

# OpenAI (used for AI wedding keepsake photo generation in photos app).
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# Image edit model: dall-e-2 (widest access) or gpt-image-1.5 (if your account has it). Set in .env.
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-2")
# Default for photos.services.openai_image_edit.edit_image_openai (falls back to OPENAI_IMAGE_MODEL).
OPENAI_IMAGE_EDIT_MODEL = os.getenv("OPENAI_IMAGE_EDIT_MODEL", "")

# Merged-photo refinement (OpenAI only; optional utility — main kiosk path uses Replicate keepsake).
OPENAI_REFINE_MODEL = os.getenv("OPENAI_REFINE_MODEL", "gpt-image-1.5")
OPENAI_REFINE_SIZE = os.getenv("OPENAI_REFINE_SIZE", "1536x1024")

# Replicate (primary keepsake generation in photos.services.keepsake_pipeline).
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")
# Preferred: full model id, e.g. black-forest-labs/flux-2-pro or zsxkib/instant-id:<version>
REPLICATE_MODEL = os.getenv("REPLICATE_MODEL", "")
# Legacy env name (still read if REPLICATE_MODEL is empty)
REPLICATE_INSTANTID_MODEL = os.getenv("REPLICATE_INSTANTID_MODEL", "")

# If true, PhotoProcessAIView uses legacy DALL-E guest-only generation instead of keepsake+Replicate.
KEEPSAKE_USE_OPENAI_LEGACY = os.getenv("KEEPSAKE_USE_OPENAI_LEGACY", "").lower() in (
    "true",
    "1",
    "yes",
)

# When True, POST /api/auth/login/ with username "kiosk" (any password) returns success without checking Django auth.
# Use for local/dev kiosk mode. Set in .env: KIOSK_SKIP_AUTH=true
KIOSK_SKIP_AUTH = os.getenv("KIOSK_SKIP_AUTH", "").lower() in ("true", "1", "yes")

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

# Celery (optional). If CELERY_BROKER_URL is unset, Railway can provide REDIS_URL for Redis-backed Celery.
default_broker = "redis://redis:6379/0" if DEBUG else ""
CELERY_BROKER_URL = (
    os.getenv("CELERY_BROKER_URL", "").strip()
    or os.getenv("REDIS_URL", "").strip()
    or default_broker
)
CELERY_RESULT_BACKEND = (
    os.getenv("CELERY_RESULT_BACKEND", "").strip()
    or CELERY_BROKER_URL
    or None
)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_TIME_LIMIT = int(os.getenv("CELERY_TASK_TIME_LIMIT", "900"))
CELERY_TASK_SOFT_TIME_LIMIT = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "840"))
CELERY_TASK_TRACK_STARTED = True
CELERY_WORKER_PREFETCH_MULTIPLIER = int(os.getenv("CELERY_WORKER_PREFETCH_MULTIPLIER", "1"))
CELERY_TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "").lower() in (
    "true",
    "1",
    "yes",
)
CELERY_TASK_EAGER_PROPAGATES = True

# Base URL for QR/download links when ``request`` is unavailable (e.g. Celery). Optional if PUBLIC_HOST is set.
API_PUBLIC_BASE_URL = os.getenv("API_PUBLIC_BASE_URL", "").strip().rstrip("/")
