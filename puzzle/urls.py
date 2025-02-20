# puzzle/urls.py
from django.urls import path
from . import views

app_name = 'puzzle'

urlpatterns = [
    # Core puzzle paths
    path('', views.home, name='home'),
    path('daily/', views.daily_puzzle, name='daily_puzzle'),
    path('submit/<int:puzzle_id>/', views.submit_solution, name='submit_solution'),
    path('puzzle/<int:puzzle_id>/', views.puzzle_detail, name='puzzle_detail'),
    path('progress/', views.user_progress, name='user_progress'),

    # Authentication paths
    path('login/', views.user_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('signup/', views.signup, name='signup'),

    
]
