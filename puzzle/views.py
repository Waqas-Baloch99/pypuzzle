<<<<<<< HEAD
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .models import Puzzle, Submission, UserProfile
from .forms import PuzzleSubmissionForm, SignUpForm, EmailAuthenticationForm
import google.generativeai as genai
from decouple import config
import json
import logging
import re

# Configure logging
logger = logging.getLogger(__name__)

# Configure Gemini API globally
genai.configure(api_key=config('GEMINI_API_KEY'))
gemini_pro = genai.GenerativeModel('gemini-pro')
gemini_mini = genai.GenerativeModel('gemini-1.5-flash')

@login_required
def index(request):
    """Display all puzzles ordered by category and level with filtering."""
    category_filter = request.GET.get('category', 'all')
    level_filter = request.GET.get('level', 'all')
    
    puzzles = Puzzle.objects.all()
    
    if category_filter != 'all':
        puzzles = puzzles.filter(category=category_filter)
    
    if category_filter != 'all' and level_filter != 'all':
        puzzles = puzzles.filter(level=level_filter)
    
    for puzzle in puzzles:
        puzzle.level_display = puzzle.get_level_display()
        puzzle.category_display = puzzle.get_category_display()
        puzzle.type_display = 'MCQ' if puzzle.puzzle_type == 'mcq' else 'Coding'
    
    return render(request, 'puzzle/index.html', {
        'puzzles': puzzles,
        'current_category': category_filter,
        'current_level': level_filter,
        'categories': Puzzle.CATEGORIES,
        'level_choices': Puzzle.LEVEL_CHOICES
    })

@login_required
def puzzle_detail(request, puzzle_id):
    """Display puzzle details and redirect to solve page for submission."""
    puzzle = get_object_or_404(Puzzle, pk=puzzle_id)
    user_profile = request.user.userprofile
    existing_submission = Submission.objects.filter(user=request.user, puzzle=puzzle).first()

    context = {
        'puzzle': puzzle,
        'submission': existing_submission,
        'is_solved': puzzle in user_profile.solved_puzzles.all(),
        'type_display': 'MCQ' if puzzle.puzzle_type == 'mcq' else 'Coding',
    }
    return render(request, 'puzzle/detail.html', context)

@login_required
def solve_puzzle(request, puzzle_id):
    """Handle puzzle solving with LLM validation for coding puzzles and allow retries."""
    puzzle = get_object_or_404(Puzzle, pk=puzzle_id)
    user_profile = request.user.userprofile
    existing_submission = Submission.objects.filter(user=request.user, puzzle=puzzle).first()
    stored_code = request.session.get(f'retry_code_{puzzle_id}', '')

    if request.method == 'POST':
        form = PuzzleSubmissionForm(request.POST, puzzle=puzzle)
        if form.is_valid():
            if existing_submission:
                submission = existing_submission
            else:
                submission = form.save(commit=False)
                submission.user = request.user
                submission.puzzle = puzzle

            if puzzle.puzzle_type == 'mcq':
                submission.answer = form.cleaned_data['answer']
                submission.status = 'completed'
            else:
                submission.code = form.cleaned_data['code']
                submission.status = 'pending'

            # Rest of validation logic remains the same
            if puzzle.puzzle_type == 'mcq':
                submission.save()
                if submission.is_correct:
                    if not existing_submission or not existing_submission.is_correct:
                        user_profile.total_points += puzzle.points
                        user_profile.puzzles_solved += 1
                        user_profile.solved_puzzles.add(puzzle)
                        user_profile.save()
                    messages.success(request, f"Correct! You earned {puzzle.points} points!")
                    return redirect('puzzle:detail', puzzle_id=puzzle_id)
                else:
                    messages.error(request, "Incorrect solution.")
                    form = PuzzleSubmissionForm(puzzle=puzzle, initial={'answer': form.cleaned_data['answer']})
            else:  # Coding puzzle
                user_code = form.cleaned_data['code']
                submission.code = user_code
                submission.status = 'pending'  # Set initial status for coding puzzles

                validation_prompt = f"""
                    Validate this Python code solution against the problem description. Respond ONLY with a JSON object.
                    Problem: {puzzle.description}
                    
                    Code:
                    ```python
                    {user_code}
                    ```
                    
                    Return a JSON object with these fields:
                    - is_valid: boolean
                    - message: string (explanation)
                    - errors: array of strings (if any)
                """

                try:
                    response = gemini_mini.generate_content(validation_prompt)
                    # Add response cleaning and better error handling
                    response_text = response.text.strip()
                    # Try to extract JSON if it's wrapped in ```json or ``` blocks
                    json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
                    if json_match:
                        response_text = json_match.group(1)
                    
                    try:
                        validation_result = json.loads(response_text)
                        logger.debug(f"Validation result: {validation_result}")
                        
                        if not isinstance(validation_result, dict):
                            raise ValueError("Validation result is not a dictionary")
                        
                        if 'is_valid' not in validation_result or 'message' not in validation_result:
                            raise ValueError("Missing required fields in validation result")
                        
                        if validation_result['is_valid']:
                            submission.is_correct = True
                            submission.status = 'completed'
                            submission.save()
                            if not existing_submission or not existing_submission.is_correct:
                                user_profile.total_points += puzzle.points
                                user_profile.puzzles_solved += 1
                                user_profile.solved_puzzles.add(puzzle)
                                user_profile.save()
                            messages.success(request, f"Correct! You earned {puzzle.points} points!")
                            return redirect('puzzle:detail', puzzle_id=puzzle_id)
                        else:
                            submission.status = 'failed'
                            submission.save()
                            error_message = validation_result.get('message', 'Invalid solution')
                            messages.error(request, f"Incorrect solution: {error_message}")
                            request.session[f'retry_code_{puzzle_id}'] = user_code
                            
                    except json.JSONDecodeError as je:
                        logger.error(f"JSON parsing error: {str(je)}\nResponse text: {response_text}")
                        messages.error(request, "Invalid response format from validation service.")
                        submission.status = 'error'
                        submission.save()
                        
                except Exception as e:
                    logger.error(f"Validation error: {str(e)}\nFull traceback:", exc_info=True)
                    messages.error(request, "An error occurred during validation. Please try again.")
                    submission.status = 'error'
                    submission.save()

    else:
        initial_data = {'code': stored_code} if stored_code else None
        form = PuzzleSubmissionForm(puzzle=puzzle, initial=initial_data)

    return render(request, 'puzzle/solve.html', {
        'form': form,
        'puzzle': puzzle,
        'submission': existing_submission
    })

@login_required
def submit_solution(request, puzzle_id):
    """Handle puzzle solution submission (alternative entry point)."""
    return puzzle_detail(request, puzzle_id)  # Reuse puzzle_detail view logic

def leaderboard(request):
    """Display the top 10 users by points."""
    top_users = UserProfile.objects.all().order_by('-total_points')[:10]
    return render(request, 'puzzle/leaderboard.html', {'top_users': top_users})

class CustomLoginView(LoginView):
    """Custom login view using email authentication."""
    form_class = EmailAuthenticationForm
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('puzzle:index')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Welcome back, {self.request.user.username}!')
        return response

def signup(request):
    """Handle user signup with custom form."""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect('puzzle:index')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def profile(request):
    user_profile = request.user.userprofile
    submissions = Submission.objects.filter(user=request.user).order_by('-submitted_at')
    context = {
        'user_profile': user_profile,
        'submissions': submissions,
        'total_points': user_profile.total_points,
        'puzzles_solved': user_profile.puzzles_solved,
    }
    return render(request, 'puzzle/profile.html', context)

def logout_view(request):
    """Handle user logout."""
    if request.method == 'POST':
        logout(request)
        messages.info(request, "You have been logged out successfully.")
    return redirect('puzzle:index')
=======
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
>>>>>>> 7c16dbc223490bb5bdec7f666aacb5bf12425ebc
