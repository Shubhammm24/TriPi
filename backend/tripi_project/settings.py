"""Django settings for the TriPi backend.

Why each setting exists is documented inline — you should be able to defend
every decision in an interview.
"""

import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (one level above backend/)
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")

# ---------------------------------------------------------------------------
# Make agent/, tools/, rag/ importable without installing them as packages.
# They live at the project root, one level above backend/.
# ---------------------------------------------------------------------------
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-change-me-before-deploying-to-production",
)

DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")

# ---------------------------------------------------------------------------
# Applications
#
# Why separate trips and accounts?
# - trips: domain logic (sessions, itineraries, agent tasks)
# - accounts: authentication concern (users, tokens)
# Single-responsibility makes each app testable and replaceable independently.
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    # Django built-ins
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",        # needed for admin login
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    # Project apps
    "accounts",
    "trips",
]

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

MIDDLEWARE = [
    # CorsMiddleware MUST be before CommonMiddleware so it can add
    # Access-Control-Allow-Origin to responses (including error responses).
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tripi_project.urls"

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

WSGI_APPLICATION = "tripi_project.wsgi.application"

# ---------------------------------------------------------------------------
# Database — PostgreSQL
#
# Why Postgres over SQLite?
# - JSONField on SQLite is text with no indexing. Postgres has native JSONB
#   with GIN indexes for querying tool_calls, preferences, etc.
# - Row-level locking for concurrent Celery workers writing to the same
#   session's itinerary table.
# - Full-text search for future "search my past trips" feature.
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "tripi"),
        "USER": os.getenv("POSTGRES_USER", "tripi"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "tripi_dev"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

# ---------------------------------------------------------------------------
# Custom User Model
#
# Django docs: "If you're starting a new project, set up a custom user model
# even if the default User model is sufficient." Changing later requires
# resetting ALL migrations.
# ---------------------------------------------------------------------------

AUTH_USER_MODEL = "accounts.CustomUser"

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ---------------------------------------------------------------------------
# Default auto field
# ---------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# CORS — allow the Next.js frontend on any origin during development.
#
# Why allow all? The existing FastAPI app had allow_origins=["*"].
# We match that behaviour so the frontend keeps working.
# In production, lock this down to the frontend's actual domain.
# ---------------------------------------------------------------------------

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Django REST Framework
#
# Why SessionAuthentication alongside JWT?
# - JWTAuthentication for the Next.js frontend (cross-origin Bearer token)
# - SessionAuthentication so the browsable API and Django admin work
# - AllowAny as default permission so unauthenticated requests still work
#   (matching FastAPI's current behaviour; auth is opt-in)
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    # Pagination: list endpoints return {count, next, previous, results}
    # instead of a flat array. Prevents unbounded queries.
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [],
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
}

# ---------------------------------------------------------------------------
# Simple JWT
# ---------------------------------------------------------------------------

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=2),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ---------------------------------------------------------------------------
# Celery — Redis as broker and result backend
#
# Why Redis?
# - Lightweight, fast, and the de facto standard for Celery brokers.
# - Also serves as the result backend so TaskStatusView can read results
#   without polling the database.
# - In production you might switch the result backend to django-db for
#   durability, but Redis is fine for dev and most production workloads.
# ---------------------------------------------------------------------------

CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
# Ensure tasks are acknowledged after completion (not before)
# so a crash mid-task causes a retry, not silent data loss.
CELERY_TASK_ACKS_LATE = True

# ---------------------------------------------------------------------------
# Google API Key — used by agent, tools, and RAG
# ---------------------------------------------------------------------------

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "trips": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
