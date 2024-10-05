#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Get DJANGO_ENV or default to 'local'
    env = os.environ.setdefault('DJANGO_ENV', 'local')

    # Map environments to their respective settings
    settings_module = {
        'production': 'kitcode.settings.production',
        'local': 'kitcode.settings.local',
    }.get(env)

    # Raise error if DJANGO_ENV is invalid
    if settings_module is None:
        raise ValueError(f"Invalid DJANGO_ENV value: {env}. Must be 'production' or 'local'.")

    # Set the appropriate settings module
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
