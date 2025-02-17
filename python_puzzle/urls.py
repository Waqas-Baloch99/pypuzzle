from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from puzzle import views

urlpatterns = [
    # Custom Admin Paths
    path('admin/puzzles/', views.manage_puzzles, name='manage_puzzles'),
    path('admin/puzzles/generate/', views.generate_puzzle, name='generate_puzzle'),
    path('admin/puzzles/test/<int:puzzle_id>/', views.test_puzzle, name='test_puzzle'),
    path('admin/puzzles/edit/<int:puzzle_id>/', views.edit_puzzle, name='edit_puzzle'),
    path('admin/puzzles/delete/<int:puzzle_id>/', views.delete_puzzle, name='delete_puzzle'),
    path('admin/puzzles/preview/<int:puzzle_id>/', views.preview_puzzle, name='preview_puzzle'),
    
    # User Management
    path('admin/users/', views.manage_users, name='manage_users'),
    
    # Dashboard
    path('admin/custom-dashboard/', views.custom_admin_dashboard, name='custom_admin_dashboard'),
    
    # Default Admin Interface
    path('admin/', admin.site.urls),
    
    # Frontend Application
    path('', include('puzzle.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)