#!/usr/bin/env python
"""Django management script for the TriPi backend."""

import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tripi_project.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Make sure it's installed and available "
            "on your PYTHONPATH, or activate a virtualenv."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
