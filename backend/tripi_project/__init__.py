"""TriPi Django project package.

Import the Celery app here so it is always available when Django starts,
ensuring that @shared_task decorators use this app instance.
"""

from .celery import app as celery_app

__all__ = ["celery_app"]
