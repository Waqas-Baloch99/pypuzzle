# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinLengthValidator

class Puzzle(models.Model):
    """
    Represents a programming puzzle with admin-controlled solutions
    """

    TEST_STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('pass', 'Approved'),
        ('fail', 'Rejected'),
    )
    deadline = models.DateTimeField(
        default=timezone.now() + timezone.timedelta(hours=24),
        help_text="Submission deadline"
    )
    title = models.CharField(
        max_length=200,
        help_text="Descriptive title for the puzzle",
        validators=[MinLengthValidator(10)]
    )
    description = models.TextField(
        help_text="Detailed problem statement and requirements",
        validators=[MinLengthValidator(50)]
    )
    examples = models.JSONField(
        default=list,
        help_text="JSON array of input/output examples [{'input': ..., 'output': ...}]"
    )
    hints = models.JSONField(
        default=list,
        help_text="JSON array of hints for solving the puzzle"
    )
    solution = models.TextField(
        help_text="Admin-only correct solution code",
        validators=[MinLengthValidator(10)]
    )
    date = models.DateField(
        default=timezone.now,
        unique=True,
        help_text="Publication date (one puzzle per day)"
    )
    test_status = models.CharField(
        max_length=10,
        choices=TEST_STATUS_CHOICES,
        default='pending',
        help_text="Approval status for publishing"
    )
    category = models.CharField(
        max_length=50,
        default="Algorithm",
        help_text="Puzzle category/type"
    )

    class Meta:
        ordering = ['-date']
        verbose_name = "Programming Puzzle"
        verbose_name_plural = "Programming Puzzles"
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['test_status']),
        ]

    def __str__(self):
        return f"{self.date}: {self.title}"

    @property
    def example_count(self):
        """Return number of examples"""
        return len(self.examples)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('puzzle:preview_puzzle', args=[str(self.id)])

class UserSubmission(models.Model):
    """
    Stores user code submissions with admin review status
    """
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('pass', 'Approved'),
        ('fail', 'Needs Revision'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='code_submissions',
        help_text="User who submitted the solution"
    )
    puzzle = models.ForeignKey(
        Puzzle,
        on_delete=models.CASCADE,
        related_name='user_submissions',
        help_text="Associated puzzle"
    )
    submitted_code = models.TextField(
        help_text="User's submitted Python code",
        validators=[MinLengthValidator(10)]
    )
    submission_date = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp of submission"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Review status"
    )
    admin_feedback = models.JSONField(
        default=dict,
        blank=True,
        help_text="LLM analysis results in JSON format"
    )

    class Meta:
        ordering = ['-submission_date']
        verbose_name = "Code Submission"
        verbose_name_plural = "Code Submissions"
        unique_together = ['user', 'puzzle']
        indexes = [
            models.Index(fields=['submission_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.puzzle.title} ({self.status})"

    @property
    def formatted_feedback(self):
        """Return structured feedback for templates"""
        return self.admin_feedback or {}

    def clean(self):
        """Validate submission before saving"""
        from django.core.exceptions import ValidationError
        if self.puzzle.test_status != 'pass':
            raise ValidationError("Cannot submit to unpublished puzzles")