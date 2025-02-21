"""
ASGI config for python_puzzle project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

<<<<<<< HEAD
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "python_puzzle.settings")
=======
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'python_puzzle.settings')
>>>>>>> 7c16dbc223490bb5bdec7f666aacb5bf12425ebc

application = get_asgi_application()
