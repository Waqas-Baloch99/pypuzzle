from django.contrib import admin
from django.urls import path, include
from puzzle import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('puzzles/', include('puzzle.urls')),
    path('daily/', views.daily_puzzle, name='daily_puzzle'),
    path('submit/<int:puzzle_id>/', views.submit_solution, name='submit_solution'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
] 