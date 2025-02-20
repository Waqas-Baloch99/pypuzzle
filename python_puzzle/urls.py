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