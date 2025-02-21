#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
<<<<<<< HEAD
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "python_puzzle.settings")
=======
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'python_puzzle.settings')
>>>>>>> 7c16dbc223490bb5bdec7f666aacb5bf12425ebc
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


<<<<<<< HEAD
if __name__ == "__main__":
=======
if __name__ == '__main__':
>>>>>>> 7c16dbc223490bb5bdec7f666aacb5bf12425ebc
    main()
