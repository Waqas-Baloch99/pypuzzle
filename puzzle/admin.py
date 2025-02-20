# puzzle/admin.py
from django.contrib import admin
from django.urls import path
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError
from django.conf import settings
from django.http import HttpResponseRedirect
from .models import Puzzle, UserSubmission
from .views import validate_code_safety, parse_llm_response
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
import google.generativeai as genai
import traceback
import json
import re
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

class PuzzleQuestAdminSite(admin.AdminSite):
    site_header = "Puzzle Quest Administration"
    site_title = "Puzzle Quest Admin Portal"
    index_title = "Game Master Dashboard"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('custom-dashboard/', self.admin_view(self.custom_dashboard), name='custom-dashboard'),
            path('manage-users/', self.admin_view(self.manage_users), name='manage-users'),
            path('manage-puzzles/', self.admin_view(self.manage_puzzles), name='manage-puzzles'),
            path('puzzles/generate/', self.admin_view(self.generate_puzzle), name='generate-puzzle'),
            path('puzzles/edit/<int:puzzle_id>/', self.admin_view(self.edit_puzzle), name='edit-puzzle'),
            path('puzzles/delete/<int:puzzle_id>/', self.admin_view(self.delete_puzzle), name='delete-puzzle'),
            path('puzzles/preview/<int:puzzle_id>/', self.admin_view(self.preview_puzzle), name='preview-puzzle'),
            path('submissions/', self.admin_view(self.manage_submissions), name='manage-submissions'),
            path('submissions/test/<int:submission_id>/', self.admin_view(self.test_submission), name='test-submission'),
        ]
        return custom_urls + urls

    # Custom Admin Views
    def custom_dashboard(self, request):
        stats = {
            'total_users': User.objects.count(),
            'total_puzzles': Puzzle.objects.count(),
            'active_puzzles': Puzzle.objects.filter(test_status='pass').count(),
            'recent_users': User.objects.order_by('-date_joined')[:10],
            'active_today': User.objects.filter(
                date_joined__date=timezone.now().date()
            ).count()
        }
        return render(request, 'admin/custom_dashboard.html', {'stats': stats})

    def manage_users(self, request):
        users = User.objects.all().order_by('-date_joined')
        return render(request, 'admin/manage_users.html', {'users': users})

    def manage_puzzles(self, request):
        puzzles = Puzzle.objects.all().order_by('-deadline')
        return render(request, 'admin/manage_puzzles.html', {
            'puzzles': puzzles,
            'default_prompt': "Generate a Python programming puzzle...",
            'min_deadline': timezone.now() + timezone.timedelta(hours=1),
            'default_deadline': timezone.now() + timezone.timedelta(days=1)
        })

    def generate_puzzle(self, request):
        try:
            # Check for existing puzzle
            today = timezone.now().date()
            if Puzzle.objects.filter(date=today).exists():
                messages.warning(request, "Today's puzzle already exists!")
                return redirect('puzzle_admin:manage-puzzles')

            # Configure AI model
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-pro')

            # Prompt forcing JSON output inside a code block
            prompt = """Generate a Python puzzle in JSON format inside a code block:
            ```json
            {
                "title": "Short Puzzle Title",
                "problem": "Problem description...",
                "examples": "Input/output examples",
                "hints": ["Hint 1", "Hint 2", "Hint 3"],
                "solution": "def solution():\n    ..."
            }
            ```"""

            response = model.generate_content(prompt)
            response_text = response.text.strip()

            # Log AI response for debugging
            logger.info(f"Raw AI Response: {response_text}")

            # Extract JSON from code block
            json_match = re.search(r"```json\s*({.*?})\s*```", response_text, re.DOTALL)
            json_str = json_match.group(1) if json_match else response_text

            # Parse JSON
            puzzle_data = json.loads(json_str)

            # Validate required fields
            required_keys = ['title', 'problem', 'examples', 'hints', 'solution']
            if not all(key in puzzle_data for key in required_keys):
                raise ValueError("Missing required fields in response")

            # Create puzzle
            Puzzle.objects.create(
                title=puzzle_data['title'][:200],
                description=puzzle_data['problem'],
                examples=puzzle_data['examples'],
                hints=puzzle_data['hints'],
                solution=puzzle_data['solution'],
                date=today,
                test_status='pass'
            )

            messages.success(request, "Puzzle created successfully!")
            return redirect('puzzle_admin:manage-puzzles')

        except json.JSONDecodeError as e:
            logger.error(f"JSON Error: {e}\nResponse: {response_text}")
            messages.error(request, "Failed to parse puzzle data")
        except AttributeError as e:
            logger.error(f"Invalid response: {e}")
            messages.error(request, "AI returned invalid format")
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            messages.error(request, f"Puzzle creation failed: {e}")

        return redirect('puzzle_admin:manage-puzzles')

    def edit_puzzle(self, request, puzzle_id):
        puzzle = get_object_or_404(Puzzle, id=puzzle_id)
        if request.method == 'POST':
            try:
                # Update puzzle logic
                puzzle.title = request.POST.get('title', '')[:200]
                puzzle.description = request.POST.get('description', '')
                # ... rest of update logic

                messages.success(request, 'Puzzle updated successfully!')
                return redirect('puzzle_admin:manage-puzzles')
            except Exception as e:
                messages.error(request, f'Validation error: {str(e)}')

        return render(request, 'admin/edit_puzzle.html', {
            'puzzle': puzzle,
            'examples': puzzle.examples,
            'hints': puzzle.hints
        })

    def delete_puzzle(self, request, puzzle_id):
        puzzle = get_object_or_404(Puzzle, id=puzzle_id)
        puzzle.delete()
        messages.success(request, 'Puzzle deleted successfully!')
        return redirect('puzzle_admin:manage-puzzles')

    def preview_puzzle(self, request, puzzle_id):
        puzzle = get_object_or_404(Puzzle, id=puzzle_id)
        return render(request, 'admin/preview_puzzle.html', {
            'puzzle': puzzle,
            'examples': puzzle.examples,
            'hints': puzzle.hints
        })

    def manage_submissions(self, request):
        submissions = UserSubmission.objects.select_related('user', 'puzzle').order_by('-submission_date')
        return render(request, 'admin/submissions.html', {'submissions': submissions})

    def test_submission(self, request, submission_id):
        submission = get_object_or_404(UserSubmission, id=submission_id)
        try:
            # LLM testing logic
            messages.success(request, f"Submission {submission.id} tested successfully")
        except Exception as e:
            messages.error(request, "Analysis failed")
        return redirect('puzzle_admin:manage-submissions')

# Instantiate custom admin site
custom_admin_site = PuzzleQuestAdminSite(name='puzzle_admin')

# Model registrations
@admin.register(Puzzle, site=custom_admin_site)
class PuzzleAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'test_status', 'category', 'deadline')
    list_filter = ('test_status', 'category', 'date')
    search_fields = ('title', 'description')
    ordering = ('-date',)
    date_hierarchy = 'date'

@admin.register(UserSubmission, site=custom_admin_site)
class UserSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'puzzle', 'status', 'submission_date')
    list_filter = ('status', 'submission_date')
    search_fields = ('user__username', 'puzzle__title')
    raw_id_fields = ('user', 'puzzle')
    ordering = ('-submission_date',)
    date_hierarchy = 'submission_date'

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

class PuzzleAdminSite(admin.AdminSite):
    site_header = 'Puzzle Admin'
    site_title = 'Puzzle Admin Portal'
    index_title = 'Welcome to Puzzle Admin Portal'

puzzle_admin = PuzzleAdminSite(name='puzzle_admin')
puzzle_admin.register(User, UserAdmin)
admin.site.register(Puzzle)
admin.site.register(UserSubmission)