# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from .models import Puzzle, UserProgress
from .forms import CustomUserCreationForm, EmailUsernameAuthForm
from multiprocessing import Process, Queue
import google.generativeai as genai
import json
import re
import ast
import logging
from datetime import date
import traceback
from .models import Puzzle, UserProgress,StudyMaterial
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django_ratelimit.decorators import ratelimit
import textwrap 
from puzzle.models import Puzzle, Category 
logger = logging.getLogger(__name__)
class SecurityError(Exception):
    """Custom security exception"""
    pass

# --------------------------
# Security Configuration
# --------------------------
FORBIDDEN_KEYWORDS = {
    'os', 'sys', 'subprocess', 'open', 'eval', 'exec',
    'shutil', 'socket', 'ctypes', 'requests', '__import__',
    'globals', 'locals', 'compile', 'memoryview', 'dir',
    'breakpoint', 'getattr', 'setattr', 'delattr', 'input'
}

SAFE_MODULES = {'math', 'random', 'datetime', 'collections', 'itertools'}

# --------------------------
# Core Utilities
# --------------------------
def validate_code_safety(code, category):  # Add category as a parameter
    """Enhanced code validation with AST analysis and category checks."""
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_KEYWORDS:
                    raise SecurityError(f"Forbidden function: {node.func.id}")
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = node.module if isinstance(node, ast.ImportFrom) else None
                names = [n.name for n in node.names]
                if module and any(part in FORBIDDEN_KEYWORDS for part in module.split('.')):
                    raise SecurityError(f"Forbidden module import: {module}")
                if any(n in FORBIDDEN_KEYWORDS for n in names):
                    raise SecurityError(f"Forbidden import: {', '.join(names)}")

        category_checks = {  # Category checks now inside the function
            'oop': [
                ('class ', "Missing class definition"),
                ('def ', "Missing method definitions")
            ],
            'file': [
                ('with open', "Should use context managers"),
                ('read(', "Missing read operation")
            ],
            'ds': [
                ('list', "List operations required"),
                ('dict', "Dictionary operations required")
            ]
        }

        for pattern, message in category_checks.get(category, []):  # Now category is defined
            if pattern not in code:
                raise SecurityError(message)

    except SyntaxError as e:
        raise SecurityError(f"Invalid syntax: {str(e)}")


# Example usage (in your generate_puzzle view, or wherever you call it):
# category = request.POST.get('category', 'basic')  # Get the category from the request
# validate_code_safety(puzzle_data['solution'], category) # Pass category to the function
import ast
import logging
import subprocess
import sys
import tempfile
import json
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)

class SecurityError(Exception):
    """Custom exception for security violations"""

def execute_safe_code(code: str, inputs: List[str], timeout: int = 3) -> List[str]:
    """Secure code execution with multiple layers of protection"""
    def validate_code_safety(code: str) -> None:
        """Deep AST analysis for security validation"""
        forbidden_nodes = {
            ast.Import, ast.ImportFrom, ast.Lambda, ast.AsyncFunctionDef,
            ast.GeneratorExp, ast.Yield, ast.YieldFrom, ast.Await
        }

        forbidden_functions = {
            'eval', 'exec', 'open', 'input', 'help', 'dir',
            'globals', 'locals', 'breakpoint', 'memoryview'
        }

        forbidden_attributes = {
            '__import__', '__builtins__', '__loader__', '__spec__',
            '__subclasses__', '__getattr__', '__setattr__'
        }

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                # Check node types
                if type(node) in forbidden_nodes:
                    raise SecurityError(f"Forbidden node type: {type(node).__name__}")

                # Check function calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in forbidden_functions:
                        raise SecurityError(f"Forbidden function: {node.func.id}")

                # Check attribute access
                if isinstance(node, ast.Attribute) and node.attr in forbidden_attributes:
                    raise SecurityError(f"Forbidden attribute: {node.attr}")

                # Check string based attacks
                if isinstance(node, ast.Str) and any(
                    kw in node.s for kw in ['__', 'import', 'sys', 'os']
                ):
                    raise SecurityError("Suspicious string pattern detected")

        except SyntaxError as e:
            raise SecurityError(f"Syntax error: {str(e)}")

    def create_sandbox(code: str, inputs: List[str]) -> str:
        """Generate secure execution wrapper"""
        return f'''
import json
import sys
from restricted_env import RestrictedEnvironment

def main():
    inputs = json.loads(sys.argv[1])
    outputs = []
    
    try:
        {code}
        
        for inp in inputs:
            try:
                result = solution(inp)
                outputs.append(str(result))
            except Exception as e:
                outputs.append(f"Error: {{str(e)}}")
                
    except Exception as e:
        outputs = [f"Runtime Error: {{str(e)}}"] * len(inputs)
    
    print(json.dumps(outputs))

if __name__ == "__main__":
    main()
'''

    try:
        # Validate code structure first
        validate_code_safety(code)

        # Create secure execution environment
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox_code = create_sandbox(code, inputs)
            script_path = Path(tmpdir) / "sandbox.py"
            
            with open(script_path, 'w') as f:
                f.write(sandbox_code)

            # Execute in isolated process
            result = subprocess.run(
                [sys.executable, str(script_path), json.dumps(inputs)],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True,
            )

            # Validate output
            try:
                outputs = json.loads(result.stdout)
                if len(outputs) != len(inputs):
                    raise ValueError("Output count mismatch")
                return outputs
            except json.JSONDecodeError:
                raise RuntimeError(f"Invalid output format: {result.stderr}")

    except subprocess.TimeoutExpired:
        raise TimeoutError(f"Execution timed out after {timeout} seconds")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Process failed: {e.stderr}")
    except SecurityError as e:
        raise
    except Exception as e:
        logger.error(f"Execution failed: {str(e)}")
        raise RuntimeError("Code execution failed")
# --------------------------
# Authentication Views
# --------------------------


def home(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('custom_admin_dashboard')
    
    categories = Category.objects.all().order_by('order') if request.user.is_authenticated else None
    
    return render(request, 'puzzle/home.html', {
        'categories': categories
    })


from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.views.decorators.http import require_http_methods
from .forms import EmailUsernameAuthForm  # Ensure this imports your custom form

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.views.decorators.http import require_http_methods
@require_http_methods(["GET", "POST"])
def user_login(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    if request.method == 'POST':
        form = EmailUsernameAuthForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            print(f"Authenticated user: {user} | Staff status: {user.is_staff}")  # Debug
            return _redirect_by_role(user)
        else:
            print("Form errors:", form.errors.as_json())  # Debug auth failures
    else:
        form = EmailUsernameAuthForm()

    return render(request, 'puzzle/auth/login.html', {'form': form})

def _redirect_by_role(user):
    if user.is_staff:
        print("Redirecting staff to admin dashboard")  # Debug
        return redirect('custom_admin_dashboard')
    print("Redirecting regular user to puzzle")  # Debug
    return redirect('puzzle:daily_puzzle')

from django.contrib.auth import login
from django.shortcuts import render, redirect

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Explicitly set the authentication backend
            user.backend = 'django.contrib.auth.backends.ModelBackend'  # or your custom backend
            
            login(request, user)
            return redirect('puzzle:daily_puzzle')
    else:
        form = CustomUserCreationForm()
    return render(request, 'puzzle/auth/signup.html', {'form': form})
# --------------------------
# User Progress Views
# --------------------------
@login_required
def user_progress(request):
    progress = UserProgress.objects.filter(user=request.user)
    return render(request, 'puzzle/progress.html', {'progress': progress})

# --------------------------
# Admin Views
# --------------------------
from puzzle.models import Puzzle, Category  # Import Category model
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@require_POST
@transaction.atomic
def generate_puzzle(request):
    try:
        # Get parameters from request
        difficulty = request.POST.get('difficulty', 'I')
        model_version = request.POST.get('model_version', 'gemini-pro')
        custom_prompt = request.POST.get('prompt', '')

        # Get or create category instance
        category_name = "daily"
        category, created = Category.objects.get_or_create(name=category_name)

        # Configure AI model
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(model_version)

        # AI Prompt for puzzle generation (EXCLUDES solution)
        ai_prompt = f'''
            Generate a Python puzzle for the daily challenge. Return **only** valid JSON:
            {{
                "title": "Puzzle Title",
                "problem": "Detailed problem statement",
                "examples": [
                    {{"input": "...", "output": "..."}},
                    {{"input": "...", "output": "..."}},
                    {{"input": "...", "output": "..."}}
                ],
                "hints": ["Hint 1", "Hint 2"]
            }}
            - Difficulty level: {difficulty}
            - Cover Python concepts (OOP, data structures, algorithms, file handling)
            - Include exactly 3 test cases with varied inputs
            - Do NOT include the solution
        '''

        # Generate puzzle content
        response = model.generate_content(ai_prompt)

        # Ensure response is received
        if not response.text:
            raise ValueError("AI response is empty.")

        raw_response = response.text.strip()

        # Log raw AI response for debugging
        logger.debug(f"Raw AI Response: {raw_response}")

        # Remove any unwanted formatting (e.g., Markdown ```json blocks)
        cleaned_json = re.sub(r'```json|```', '', raw_response).strip()

        # Attempt to parse JSON
        try:
            puzzle_data = json.loads(cleaned_json)
        except json.JSONDecodeError:
            logger.error(f"JSON Decode Error. AI Response: {raw_response}")
            messages.error(request, 'Invalid AI response format. Please check AI response.')
            return redirect('manage_puzzles')

        # Validate required fields (EXCLUDES solution)
        required_fields = ['title', 'problem', 'examples', 'hints']
        if not all(field in puzzle_data for field in required_fields):
            logger.error(f"Missing fields in AI response: {puzzle_data}")
            messages.error(request, 'AI response is missing required fields.')
            return redirect('manage_puzzles')

        # Create puzzle in database (NO solution field)
        Puzzle.objects.create(
            title=puzzle_data['title'][:200],
            description=puzzle_data['problem'],
            examples=json.dumps(puzzle_data['examples']),
            hints=json.dumps(puzzle_data['hints']),
            difficulty=difficulty,
            category=category,  # Assign Category instance instead of string
            date=timezone.now().date(),
            test_status='pending'
        )

        messages.success(request, 'Daily puzzle generated successfully!')

    except Exception as e:
        logger.error(f"Generation failed: {traceback.format_exc()}")
        messages.error(request, f'Generation failed: {str(e)}')

    return redirect('manage_puzzles')

@staff_member_required
def test_puzzle(request, puzzle_id):
    puzzle = get_object_or_404(Puzzle, id=puzzle_id)
    try:
        examples = json.loads(puzzle.examples)
        inputs = [ex.get('input') for ex in examples]
        expected_outputs = [str(ex.get('output')) for ex in examples]
        
        wrapped_code = f"def solution(input):\n    {puzzle.solution}"
        actual_outputs = execute_safe_code(wrapped_code, inputs)
        
        test_results = []
        all_passed = True
        for inp, exp, act in zip(inputs, expected_outputs, actual_outputs):
            passed = act == exp
            test_results.append({
                'input': inp,
                'expected': exp,
                'actual': act,
                'passed': passed
            })
            if not passed:
                all_passed = False
                
        puzzle.test_status = 'pass' if all_passed else 'fail'
        puzzle.test_results = json.dumps(test_results)
        puzzle.save()
        messages.success(request, f"Test complete: {'All passed' if all_passed else 'Some failures'}")
            
    except TimeoutError:
        puzzle.test_status = 'fail'
        puzzle.save()
        messages.error(request, 'Test timed out - check for infinite loops')
    except SecurityError as e:
        puzzle.test_status = 'fail'
        puzzle.save()
        messages.error(request, f'Security violation: {str(e)}')
    except Exception as e:
        logger.error(f"Test failed: {traceback.format_exc()}")
        messages.error(request, f'Test failed: {str(e)}')
        puzzle.test_status = 'error'
        puzzle.save()
        
    return redirect('manage_puzzles')

@staff_member_required
def manage_puzzles(request):
    puzzle_list = Puzzle.objects.all().order_by('-date')
    paginator = Paginator(puzzle_list, 25)
    page_number = request.GET.get('page')
    puzzles = paginator.get_page(page_number)
    return render(request, 'admin/manage_puzzles.html', {
        'puzzles': puzzles,
        'today': timezone.now().date(),
        'model_versions': ['gemini-pro', 'gemini-ultra']
    })
@staff_member_required
def edit_puzzle(request, puzzle_id):
    puzzle = get_object_or_404(Puzzle, id=puzzle_id)
    if request.method == 'POST':
        try:
            # Validate and update puzzle
            puzzle.title = request.POST.get('title', '')[:200]
            puzzle.description = request.POST.get('description', '')
            puzzle.difficulty = request.POST.get('difficulty', 'I')
            puzzle.examples = json.dumps(json.loads(request.POST.get('examples', '[]')))
            puzzle.hints = json.dumps(json.loads(request.POST.get('hints', '[]')))
            
            new_solution = request.POST.get('solution', '')
            validate_code_safety(new_solution)
            puzzle.solution = new_solution
            
            puzzle.save()
            messages.success(request, 'Puzzle updated successfully!')
            return redirect('manage_puzzles')
        except (json.JSONDecodeError, SecurityError) as e:
            messages.error(request, f'Validation error: {str(e)}')
    
    return render(request, 'admin/edit_puzzle.html', {
        'puzzle': puzzle,
        'examples': json.loads(puzzle.examples),
        'hints': json.loads(puzzle.hints)
    })

@staff_member_required
@require_POST
def delete_puzzle(request, puzzle_id):
    puzzle = get_object_or_404(Puzzle, id=puzzle_id)
    puzzle.delete()
    messages.success(request, 'Puzzle deleted successfully!')
    return redirect('manage_puzzles')

@staff_member_required
def preview_puzzle(request, puzzle_id):
    puzzle = get_object_or_404(Puzzle, id=puzzle_id)
    return render(request, 'admin/preview_puzzle.html', {
        'puzzle': puzzle,
        'examples': json.loads(puzzle.examples),
        'hints': json.loads(puzzle.hints),
        'test_results': json.loads(puzzle.test_results) if puzzle.test_results else []
    })

@staff_member_required
def manage_users(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin/manage_users.html', {'users': users})

from django.utils import timezone

from django.shortcuts import render
from django.utils import timezone
from django.urls import reverse
from .models import User, Puzzle, Category

from django.urls import reverse
from django.shortcuts import render
from .models import User, Puzzle, Category  # Ensure that these are the correct imports

def custom_admin_dashboard(request):
    # Prepare the statistics and other data
    stats = {
        'total_users': User.objects.count(),
        'total_puzzles': Puzzle.objects.count(),
        'active_puzzles': Puzzle.objects.filter(test_status='pass').count(),
        'users': User.objects.order_by('-date_joined')[:10],
        'active_today': User.objects.filter(
            date_joined__date=timezone.now().date()
        ).count()
    }
    
    # Reverse URL for 'study_category_add' with the correct namespace
    add_category_url = reverse('puzzle:study_category_add')  # Use the namespace here
    
    # Pass stats, categories, and add_category_url to the template
    return render(request, 'admin/custom_dashboard.html', {
        'stats': stats,
        'categories': Category.objects.all().order_by('order'),
        'add_category_url': add_category_url  # Pass the URL to the template
    })


# --------------------------
# Puzzle Views
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import transaction
from django.contrib import messages
import json
from .models import Puzzle
import logging

logger = logging.getLogger(__name__)

@login_required
def daily_puzzle(request):
    today = timezone.now().date()
    try:
        # Get the latest puzzle for today
        puzzle = Puzzle.objects.filter(date=today).latest('id')
        
        # Prepare data for template
        context = {
            'puzzle': puzzle,
            'examples': json.loads(puzzle.examples),
            'hints': json.loads(puzzle.hints),
            'concepts': puzzle.concepts.split(',') if puzzle.concepts else []
        }
        
        return render(request, 'puzzle/daily_puzzle.html', context)

    except ObjectDoesNotExist:
        # Create new puzzle if none exists
        try:
            with transaction.atomic():
                create_daily_puzzle()
                messages.success(request, "⚔️ New quest generated! ⚔️")
                return redirect('puzzle:daily_puzzle')
        except Exception as e:
            logger.error(f"Daily puzzle creation failed: {str(e)}")
            messages.error(request, "🛡️ Failed to generate today's quest")
            return redirect('puzzle:home')
    
    except MultipleObjectsReturned:
        # Handle duplicate puzzles
        latest_puzzle = Puzzle.objects.filter(date=today).latest('id')
        messages.warning(request, "⚡ Multiple scrolls found - showing latest")
        return redirect('puzzle:daily_puzzle')

import json
import logging
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Puzzle, UserProgress

logger = logging.getLogger(__name__)

@login_required
@require_POST
@transaction.atomic
def submit_solution(request, puzzle_id):
    puzzle = get_object_or_404(Puzzle, id=puzzle_id)
    progress, created = UserProgress.objects.get_or_create(
        user=request.user,
        puzzle=puzzle,
        defaults={'attempts': 0, 'solved': False}
    )

    try:
        user_code = request.POST.get('solution', '').strip()
        if not user_code:
            raise ValueError("Empty code submission")

        # Initialize Gemini API
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')

        # Construct the prompt with explicit JSON structure instructions
        prompt = f"""
        Compare the following user-provided Python code to the correct solution:

        User Code:
        ```python
        {user_code}
        ```

        Correct Solution:
        ```python
        {puzzle.solution}
        ```

        Instructions:
        - Determine if the user's code is functionally equivalent to the correct solution.
        - Respond with a JSON object containing a single key 'correct' with a boolean value.
        - Do not include any markdown formatting, comments, or extra text.
        - Example response for correct code: {{"correct": true}}
        - Example response for incorrect code: {{"correct": false}}
        """

        # Generate content with Gemini
        response = model.generate_content(prompt)
        logger.info(f"Raw Gemini response: {response.text}")

        # Parse and validate the response
        try:
            gemini_response = json.loads(response.text.strip())
            
            # Ensure the response is a dictionary
            if not isinstance(gemini_response, dict):
                raise ValueError("Response is not a JSON object")
            
            is_correct = gemini_response.get('correct', False)
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            logger.error(f"Response content: {response.text}")
            raise ValueError("Invalid response format from Gemini")

        # Update user progress
        progress.attempts += 1
        if is_correct:
            progress.solved = True
            progress.solved_date = timezone.now()
            messages.success(request, "🎉 Correct!")
        else:
            messages.warning(request, "Incorrect.")
        progress.save()

    except ValueError as e:
        messages.error(request, f"Invalid input: {str(e)}")
    except Exception as e:
        logger.error(f"Error in puzzle {puzzle_id}: {str(e)}", exc_info=True)
        messages.error(request, "💥 An error occurred. Please try again.")

    return redirect('puzzle:daily_puzzle')
# --------------------------
# Helper Functions
# --------------------------
def create_daily_puzzle():
    try:
        today = date.today()
        if Puzzle.objects.filter(date=today).exists():
            return
            
        puzzle_data = generate_ai_puzzle()
        if not puzzle_data:
            puzzle_data = {
                'title': 'Reverse String',
                'problem': 'Write a function to reverse a string',
                'examples': [{'input': '"hello"', 'output': 'olleh'}],
                'hints': ['Use slicing', 'Try negative step'],
                'solution': 'return input[::-1]',
                'difficulty': 'B'
            }
            
        Puzzle.objects.create(
            title=puzzle_data['title'],
            description=puzzle_data['problem'],
            examples=json.dumps(puzzle_data['examples']),
            hints=json.dumps(puzzle_data['hints']),
            solution=puzzle_data['solution'],
            difficulty=puzzle_data['difficulty'],
            date=today,
            test_status='pass'
        )
    except Exception as e:
        logger.error(f"Daily puzzle failed: {traceback.format_exc()}")

def generate_ai_puzzle():
    """Stub for AI puzzle generation (implement your actual logic here)"""
    return None

@require_POST
def custom_logout(request):
    logout(request)
    return redirect('puzzle:login')
# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .forms import CategoryForm
from .models import Category, StudyMaterial


def study_category(request, category_code):
    category = get_object_or_404(Category, code=category_code)
    materials = category.materials.all().order_by('order')  # Fetch all related study materials for the category
    return render(request, 'puzzle/study/category.html', {
        'category': category,
        'materials': materials
    })

def study_material(request, category_code, material_order):
    material = get_object_or_404(
        StudyMaterial, 
        category__code=category_code, 
        order=material_order
    )
    return render(request, 'puzzle/study/category.html', {
        'material': material
    })

@staff_member_required
def add_study_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, "Category added successfully!")
            return redirect('manage_categories')  # Change this to the actual URL name
        else:
            messages.error(request, "Form has errors")
    else:
        form = CategoryForm()
    return render(request, 'admin/add_category.html', {'form': form})
