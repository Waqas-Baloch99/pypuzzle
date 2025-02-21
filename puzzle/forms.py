from django import forms
<<<<<<< HEAD
from .models import Submission, Puzzle
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class PuzzleSubmissionForm(forms.ModelForm):
    code = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control mb-3',
            'placeholder': 'Enter your code here',
            'rows': 6
        }),
        required=False
    )
    answer = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control mb-3',
            'placeholder': 'Enter your answer'
        })
    )

    class Meta:
        model = Submission
        fields = ['code', 'answer']

    def __init__(self, *args, **kwargs):
        self.puzzle = kwargs.pop('puzzle', None)
        super().__init__(*args, **kwargs)
        if self.puzzle:
            if self.puzzle.puzzle_type == 'mcq':
                # Use test_cases for MCQ choices
                self.fields['answer'].widget = forms.Select(
                    choices=[('', 'Select an option')] + [(k, v) for k, v in self.puzzle.test_cases.items()],
                    attrs={'class': 'form-control mb-3'}
                )
                self.fields['code'].widget = forms.HiddenInput()
            else:
                self.fields['answer'].widget = forms.HiddenInput()
                # No reliance on template_code; initial code set by view via stored_code

    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get('code')
        answer = cleaned_data.get('answer')

        if self.puzzle:
            if self.puzzle.puzzle_type == 'mcq':
                if not answer:
                    raise forms.ValidationError("Please select an answer for this MCQ.")
                if answer not in self.puzzle.test_cases.keys():
                    raise forms.ValidationError("Answer must be one of the provided options.")
            else:
                if not code:
                    raise forms.ValidationError("Please provide code for this coding puzzle.")
        else:
            if not code and not answer:
                raise forms.ValidationError("Either code or answer must be provided.")

        return cleaned_data

class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control mb-3'})
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control mb-3'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control mb-3'})
    )
=======
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db import transaction
from django.core.exceptions import ValidationError
import re
from .models import Category
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Required. Unique.")
    first_name = forms.CharField(required=True, max_length=25)
    last_name = forms.CharField(required=True, max_length=25)
>>>>>>> 7c16dbc223490bb5bdec7f666aacb5bf12425ebc

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
<<<<<<< HEAD
            raise ValidationError("Email already exists")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        base_username = f"{self.cleaned_data['first_name'].lower()}.{self.cleaned_data['last_name'].lower()}"
        username = base_username
        counter = 1
        
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
            
        user.username = username
=======
            raise ValidationError("This email is already registered.")
        return email

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.generate_username()
        user.email = self.cleaned_data['email']
>>>>>>> 7c16dbc223490bb5bdec7f666aacb5bf12425ebc
        if commit:
            user.save()
        return user

<<<<<<< HEAD
class EmailAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Email or Username',
        widget=forms.TextInput(attrs={
            'class': 'form-control mb-3',
            'placeholder': 'Enter email or username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control mb-3',
            'placeholder': 'Enter password'
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if '@' in username:
            try:
                user = User.objects.get(email=username)
                return user.username
            except User.DoesNotExist:
                raise ValidationError("Invalid email address")
        return username
=======
    def generate_username(self):
        first = re.sub(r'[^a-zA-Z0-9_]', '', self.cleaned_data['first_name']).lower()[:15]
        last = re.sub(r'[^a-zA-Z0-9_]', '', self.cleaned_data['last_name']).lower()[:15]
        base = f"{first}{last}".strip('_')
        
        counter = 1
        max_attempts = 100
        while counter <= max_attempts:
            username = f"{base}{counter if counter > 1 else ''}"
            if not User.objects.filter(username=username).exists():
                return username
            counter += 1
        raise ValidationError("Unable to generate unique username. Try again.")

class EmailUsernameAuthForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email or Username'

    def clean(self):
        username_or_email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if '@' in username_or_email:
            users = User.objects.filter(email=username_or_email)
            if users.count() == 0:
                raise ValidationError("Invalid email or password.")
            elif users.count() > 1:
                raise ValidationError("Multiple accounts with this email exist. Use username instead.")
            self.cleaned_data['username'] = users.first().username

        return super().clean()
    # Form for adding a new Study Category
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'code', 'order']  # Adjust the fields as per your model

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if Category.objects.filter(code=code).exists():
            raise ValidationError("This category code already exists.")
        return code
    from django import forms
from .models import Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['code', 'name', 'description', 'order', 'icon_class']
>>>>>>> 7c16dbc223490bb5bdec7f666aacb5bf12425ebc
