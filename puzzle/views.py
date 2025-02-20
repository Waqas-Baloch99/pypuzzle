# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta  # Add this import
import google.generativeai as genai
import traceback  # <-- Add this
import json
import re
import logging
import ast
from django.contrib.auth.models import User
from .models import Puzzle, UserSubmission

logger = logging.getLogger(__name__)

# --------------------------
# Security Configuration
# --------------------------
FORBIDDEN_KEYWORDS = {
    'os', 'sys', 'subprocess', 'open', 'eval', 'exec',
    'shutil', 'socket', 'ctypes', 'requests', '__import__',
    'globals', 'locals', 'compile', 'memoryview', 'dir',
    'breakpoint', 'getattr', 'setattr', 'delattr', 'input'
}

class SecurityError(Exception):
    pass

# --------------------------
# Core Views
# --------------------------

@login_required
def home(request):
    """Display active puzzles for regular users"""
    puzzles = Puzzle.objects.filter(test_status='pass').order_by('-date')
    return render(request, 'puzzle/home.html', {'puzzles': puzzles})

@login_required
def daily_puzzle(request):
    """Display the daily puzzle"""
    today = timezone.now().date()
    puzzle = Puzzle.objects.filter(date=today, test_status='pass').first()
    if not puzzle:
        messages.info(request, "No daily puzzle available yet.")
    return render(request, 'puzzle/daily_puzzle.html', {'puzzle': puzzle})
@login_required
@require_POST
@transaction.atomic
def submit_solution(request, puzzle_id):
    """Handle user code submissions with restrictions"""
    puzzle = get_object_or_404(Puzzle, id=puzzle_id)
    user_code = request.POST.get('solution', '').strip()

    # Deadline check
    if timezone.now() > puzzle.deadline:
        messages.error(request, "⏳ Submission deadline has passed")
        return redirect('puzzle:puzzle_detail', puzzle_id=puzzle_id)

    # Check for existing successful submission
    if UserSubmission.objects.filter(
        user=request.user,
        puzzle=puzzle,
        status='pass'
    ).exists():
        messages.warning(request, "🎉 You've already conquered this quest!")
        return redirect('puzzle:puzzle_detail', puzzle_id=puzzle_id)

    # Validate code presence
    if not user_code:
        messages.error(request, "❌ Empty code submission")
        return redirect('puzzle:puzzle_detail', puzzle_id=puzzle_id)

    try:
        # Security validation
        validate_code_safety(user_code)
        
        # Create new submission
        UserSubmission.objects.create(
            user=request.user,
            puzzle=puzzle,
            submitted_code=user_code,
            status='pending'
        )
        messages.success(request, "⚡ Solution submitted for alchemy review!")

    except SecurityError as e:
        messages.error(request, f"🛡️ Forbidden magic: {str(e)}")
    except Exception as e:
        logger.error(f"Submission error: {str(e)}", exc_info=True)
        messages.error(request, "💥 Spell casting failed")

    return redirect('puzzle:puzzle_detail', puzzle_id=puzzle_id)
from django.db.models import Count

@login_required
def user_progress(request):
    """Display user progress with attempt counts"""
    submissions = UserSubmission.objects.filter(
        user=request.user
    ).annotate(
        attempt_count=Count('puzzle')
    ).order_by('-submission_date')
    
    total_solved = submissions.filter(status='pass').count()
    
    return render(request, 'puzzle/progress.html', {
        'submissions': submissions,
        'total_solved': total_solved
    })

from django.shortcuts import get_object_or_404
from .models import Puzzle  # Make sure you import your Puzzle model

# views.py
def puzzle_detail(request, puzzle_id):
    puzzle = get_object_or_404(Puzzle, id=puzzle_id)
    now = timezone.now()
    
    context = {
        'puzzle': puzzle,
        'time_remaining': (puzzle.deadline - now).total_seconds() if puzzle.deadline else 0,
        'submission_count': UserSubmission.objects.filter(
            user=request.user,
            puzzle=puzzle
        ).count(),
        'examples': puzzle.examples,
        'test_results': puzzle.test_results if hasattr(puzzle, 'test_results') else None
    }
    return render(request, 'puzzle/daily_puzzle.html', context)
# --------------------------
# Authentication Views
# --------------------------

def user_login(request):
    """Handle user login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Logged in successfully!")
            return redirect('puzzle:home')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'puzzle/auth/login.html')

def signup(request):
    """Handle user signup"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('puzzle:home')

    return render(request, 'puzzle/auth/signup.html')

def custom_logout(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('puzzle:login')

# --------------------------
# Admin Views
# --------------------------
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render


@staff_member_required
def custom_admin_dashboard(request):
    stats = {
        'total_users': User.objects.count(),
        'total_puzzles': Puzzle.objects.count(),
        'active_puzzles': Puzzle.objects.filter(test_status='pass').count(),
        'users': User.objects.order_by('-date_joined')[:10],
        'active_today': User.objects.filter(
            date_joined__date=timezone.now().date()
        ).count()
    }
    return render(request, 'admin/custom_dashboard.html', {'stats': stats})
def manage_users(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin/manage_users.html', {'users': users})

@staff_member_required
def manage_submissions(request):
    """Admin view for submitted solutions"""
    submissions = UserSubmission.objects.select_related('user', 'puzzle').order_by('-submitted_at')
    return render(request, 'admin/submissions.html', {'submissions': submissions})


# --------------------------
# Puzzle Management
# --------------------------

# views.py
# views.py




# --------------------------
# Helper Functions
# --------------------------

def validate_code_safety(code):
    """Basic code security validation"""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_KEYWORDS:
                raise SecurityError(f"Forbidden function: {node.func.id}")

def parse_llm_response(text):
    """Parse LLM JSON response with error handling"""
    try:
        cleaned = re.sub(r'```json|```', '', text).strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse LLM response: {text}")
        return {'error': 'Invalid response format'}