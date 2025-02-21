<<<<<<< HEAD
from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from django.contrib.auth import views as auth_views

app_name = 'puzzle'
urlpatterns = [
    path('', views.index, name='index'),
    path('puzzle/<int:puzzle_id>/', views.puzzle_detail, name='detail'),
    path('puzzle/<int:puzzle_id>/solve/', views.solve_puzzle, name='solve'),
    path('puzzle/<int:puzzle_id>/submit/', views.submit_solution, name='submit'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('signup/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('logout/', LogoutView.as_view(), name='logout'),  # Updated logout view
]
=======
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
>>>>>>> 7c16dbc223490bb5bdec7f666aacb5bf12425ebc
