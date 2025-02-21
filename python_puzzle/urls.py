<<<<<<< HEAD
"""
URL configuration for python_puzzle project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from puzzle.admin import custom_admin_site

urlpatterns = [
    # Default Django Admin
    path('admin/', admin.site.urls),

    # Custom Admin Panel
    path('custom-admin/', custom_admin_site.urls),

    # Puzzle App URLs
    path('', include('puzzle.urls')),

    # Authentication URLs
    path('accounts/', include('django.contrib.auth.urls')),
]

# Serving media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
=======
# project/urls.py
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin  # Added missing import
from puzzle.admin import custom_admin_site as puzzle_admin  # Removed trailing comma

urlpatterns = [
    path('custom-admin/', puzzle_admin.urls),
    path('admin/', admin.site.urls),
    path('', include('puzzle.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
>>>>>>> 7c16dbc223490bb5bdec7f666aacb5bf12425ebc
