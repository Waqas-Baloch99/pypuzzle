from django import forms
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

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.generate_username()
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

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
