# puzzle/urls.py
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from .views import custom_logout

app_name = 'puzzle'

urlpatterns = [
    # Frontend paths
    path('', views.home, name='home'),
    path('daily/', views.daily_puzzle, name='daily_puzzle'),
    path('submit/<int:puzzle_id>/', views.submit_solution, name='submit_solution'),
    path('progress/', views.user_progress, name='user_progress'),
    
    # Authentication paths (customized)
    path('login/', views.user_login, name='login'),
    path('logout/', custom_logout, name='logout'),
    path('signup/', views.signup, name='signup'),
    
    # Password reset paths with custom templates
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='puzzle/auth/password_reset_form.html',
             email_template_name='puzzle/auth/password_reset_email.html'
         ), 
         name='password_reset'),
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='puzzle/auth/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='puzzle/auth/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='puzzle/auth/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    path('study/<str:category_code>/', views.study_category, name='study_category'),
    path('admin/study-category/add/', views.add_study_category, name='study_category_add'),
    path('study/<str:category_code>/<int:material_order>/', views.study_material, name='study_material'),
]