"""Celery application for the TriPi backend.

Why Celery?
- Agent runs take 30-60 seconds and call 8+ external APIs.
- Tying up a Django web worker for that long is a scalability anti-pattern:
  with 4 Gunicorn workers, 4 concurrent requests would exhaust the pool.
- Celery lets us offload agent work to a separate process pool that scales
  independently from web request handling.
- Bonus: retry logic, rate limiting, dead-letter queues, and monitoring
  (Flower) come for free.

This module is imported by tripi_project/__init__.py so that the Celery app
is always available when Django starts (required for @shared_task discovery).
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tripi_project.settings")

app = Celery("tripi_project")

# Read Celery config from Django settings (all keys prefixed with CELERY_)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in each installed app
app.autodiscover_tasks()
