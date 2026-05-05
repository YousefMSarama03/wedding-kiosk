"""
Django settings for app project.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me-in-production")

DEBUG = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
# If set, QR download URLs use this host so phones on the same network can reach the backend.
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "").strip()
PUBLIC_SCHEME = os.getenv("PUBLIC_SCHEME", "http").strip() or "http"
PUBLIC_PORT = os.getenv("PUBLIC_PORT", "8000").strip()
if PUBLIC_HOST and PUBLIC_HOST not in ALLOWED_HOSTS:
    ALLOWED_HOSTS = list(ALLOWED_HOSTS) + [PUBLIC_HOST]

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

CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
# Required for session auth when frontend and backend are on different origins (e.g. production).
CORS_ALLOW_CREDENTIALS = True

# Required in Django 4+ when frontend (e.g. localhost:3000) sends requests to the API (localhost:8000).
# The browser sends Origin: http://localhost:3000; Django CSRF checks it against this list.
CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",")

# OpenAI (used for AI wedding keepsake photo generation in photos app).
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# Image edit model: dall-e-2 (widest access) or gpt-image-1.5 (if your account has it). Set in .env.
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-2")
# Default for photos.services.openai_image_edit.edit_image_openai (falls back to OPENAI_IMAGE_MODEL).
OPENAI_IMAGE_EDIT_MODEL = os.getenv("OPENAI_IMAGE_EDIT_MODEL", "")

# Merged-photo refinement (OpenAI only; optional utility — main kiosk path uses Replicate keepsake).
OPENAI_REFINE_MODEL = os.getenv("OPENAI_REFINE_MODEL", "gpt-image-1.5")
OPENAI_REFINE_SIZE = os.getenv("OPENAI_REFINE_SIZE", "1536x1024")

# Replicate InstantID (primary keepsake generation in photos.services.keepsake_pipeline).
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")
# Optional override, e.g. lucataco/... version hash or zsxkib/instant-id:...
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
