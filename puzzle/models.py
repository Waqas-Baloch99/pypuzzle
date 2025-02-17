# puzzle/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    CODE_CHOICES = (
        ('basic', 'Basic Python'),
        ('oop', 'Object-Oriented Programming'),
        ('ds', 'Data Structures'),
        ('file', 'File Handling'),
    )
    
    code = models.CharField(max_length=10, choices=CODE_CHOICES, primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)
    icon_class = models.CharField(max_length=50, default='bi-journal-bookmark')

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order']

    def __str__(self):
        return self.name
  
class Puzzle(models.Model):
    DIFFICULTY_CHOICES = (
        ('B', 'Beginner'),
        ('I', 'Intermediate'),
        ('A', 'Advanced'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    examples = models.JSONField(default=list)
    hints = models.JSONField(default=list)
    solution = models.TextField()
    difficulty = models.CharField(
        max_length=1, 
        choices=DIFFICULTY_CHOICES, 
        default='I'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        to_field='code',
        default='basic'
    )
    date = models.DateField(default=timezone.now)
    test_status = models.CharField(
        max_length=10,
        choices=(
            ('pending', 'Pending'), 
            ('pass', 'Passed'), 
            ('fail', 'Failed')
        ),
        default='pending'
    )
    test_results = models.JSONField(null=True, blank=True)
    concepts = models.CharField(
        max_length=255,
        blank=True,
        default="Variables, Functions, Control Flow",
        help_text="Comma-separated list of learning concepts"
    )

    def __str__(self):
        return self.title

    def get_category_display_name(self):
        return self.category.name

class StudyMaterial(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.category.name}: {self.title}"

class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    puzzle = models.ForeignKey(Puzzle, on_delete=models.CASCADE, related_name='user_progress')
    solved = models.BooleanField(default=False)
    solved_date = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [['user', 'puzzle']]
        verbose_name_plural = 'User Progress Records'

    def __str__(self):
        return f"{self.user.username} - {self.puzzle.title}"
    
    def success_rate(self):
        if self.attempts > 0:
            return round((int(self.solved) / self.attempts) * 100, 2)
        return 0.0