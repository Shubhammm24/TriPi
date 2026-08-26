"""Test-only Django settings that override the database to SQLite.

Why a separate test settings file?
- Production/dev uses PostgreSQL (JSONB indexes, row-level locking).
- Tests need to run without Docker/Postgres (CI environments, offline dev).
- SQLite is in-memory, fast, and requires zero setup.
- pytest-django creates/destroys the test DB automatically.

Usage:
    py -3 -m pytest --ds=tripi_project.test_settings -v
"""

from tripi_project.settings import *  # noqa: F401,F403

# Override database to SQLite in-memory for tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Speed up password hashing in tests (don't need security, need speed)
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable Celery task execution in tests — tasks run synchronously
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
