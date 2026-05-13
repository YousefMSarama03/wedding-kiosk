"""
Django settings for app project.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_csv(name: str, default: str) -> list[str]:
    return [p.strip() for p in os.getenv(name, default).split(",") if p.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me-in-production")

DEBUG = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = _env_csv("ALLOWED_HOSTS", "localhost,127.0.0.1")
# Optional: comma-separated extra hosts.
for _extra in os.getenv("DJANGO_EXTRA_ALLOWED_HOSTS", "").split(","):
    _extra = _extra.strip()
    if _extra and _extra not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_extra)
# Railway and similar: accept any *.up.railway.app host (hostname only, no scheme).
if os.getenv("ALLOW_RAILWAY_HOSTS", "true").lower() in ("true", "1", "yes"):
    if ".up.railway.app" not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(".up.railway.app")

# If set, QR download URLs use this host so phones can reach the backend.
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "").strip()
PUBLIC_SCHEME = os.getenv("PUBLIC_SCHEME", "http").strip() or "http"
PUBLIC_PORT = os.getenv("PUBLIC_PORT", "8000").strip()
if PUBLIC_HOST and PUBLIC_HOST not in ALLOWED_HOSTS:
    ALLOWED_HOSTS = list(ALLOWED_HOSTS) + [PUBLIC_HOST]

# Trust X-Forwarded-Proto from reverse proxy (Railway / nginx).
if os.getenv("USE_X_FORWARDED_PROTO", "").lower() in ("true", "1", "yes"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Secure cookies in production (HTTPS).
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

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
    "whitenoise.middleware.WhiteNoiseMiddleware",
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

# Railway / Heroku: DATABASE_URL. Local: POSTGRES_* discrete vars.
if os.getenv("DATABASE_URL", "").strip():
    DATABASES = {
        "default": dj_database_url.config(
            conn_max_age=int(os.getenv("DATABASE_CONN_MAX_AGE", "600")),
            ssl_require=os.getenv("DATABASE_SSL_REQUIRE", "").lower() in ("true", "1", "yes"),
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "wedding_kiosk"),
            "USER": os.getenv("POSTGRES_USER", "postgres"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "postgres"),
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

# WhiteNoise for static files in production (collectstatic required at deploy).
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedStaticFilesStorage"
        ),
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = _env_csv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = _env_csv(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)
_FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "").strip()
if _FRONTEND_ORIGIN:
    if _FRONTEND_ORIGIN not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS = list(CORS_ALLOWED_ORIGINS) + [_FRONTEND_ORIGIN]
    if _FRONTEND_ORIGIN not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS = list(CSRF_TRUSTED_ORIGINS) + [_FRONTEND_ORIGIN]

# OpenAI (used for AI wedding keepsake photo generation in photos app).
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-2")
OPENAI_IMAGE_EDIT_MODEL = os.getenv("OPENAI_IMAGE_EDIT_MODEL", "")

OPENAI_REFINE_MODEL = os.getenv("OPENAI_REFINE_MODEL", "gpt-image-1.5")
OPENAI_REFINE_SIZE = os.getenv("OPENAI_REFINE_SIZE", "1536x1024")

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "").strip() or os.getenv(
    "PUBLIC_REPLICATE_API_TOKEN", ""
).strip()
REPLICATE_MODEL = os.getenv("REPLICATE_MODEL", "")
REPLICATE_INSTANTID_MODEL = os.getenv("REPLICATE_INSTANTID_MODEL", "")

KEEPSAKE_USE_OPENAI_LEGACY = os.getenv("KEEPSAKE_USE_OPENAI_LEGACY", "").lower() in (
    "true",
    "1",
    "yes",
)

KIOSK_SKIP_AUTH = os.getenv("KIOSK_SKIP_AUTH", "").lower() in ("true", "1", "yes")

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

CELERY_BROKER_URL = (
    os.getenv("CELERY_BROKER_URL", "").strip()
    or os.getenv("REDIS_URL", "").strip()
)
CELERY_RESULT_BACKEND = (
    os.getenv("CELERY_RESULT_BACKEND", "").strip() or CELERY_BROKER_URL or None
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

API_PUBLIC_BASE_URL = os.getenv("API_PUBLIC_BASE_URL", "").strip().rstrip("/")
