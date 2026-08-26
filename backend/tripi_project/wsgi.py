"""WSGI config for the TriPi Django project.

Gunicorn uses this as its entry point:
    gunicorn tripi_project.wsgi:application --bind 0.0.0.0:8000
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tripi_project.settings")

application = get_wsgi_application()
