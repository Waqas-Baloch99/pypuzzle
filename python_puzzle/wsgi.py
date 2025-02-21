<<<<<<< HEAD
"""
WSGI config for python_puzzle project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "python_puzzle.settings")

application = get_wsgi_application()
=======
# Should look like this:
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'python_puzzle.settings')
application = get_wsgi_application()
>>>>>>> 7c16dbc223490bb5bdec7f666aacb5bf12425ebc
