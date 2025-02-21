# puzzle/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.core.exceptions import MultipleObjectsReturned

User = get_user_model()

class EmailUsernameAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        try:
            # Case-insensitive lookup with normalization
            normalized_username = username.strip().lower()
            user = User.objects.get(
                Q(username__iexact=normalized_username) |
                Q(email__iexact=normalized_username)
            )
        except User.DoesNotExist:
            # No user found - return None to try next backend
            return None
        except MultipleObjectsReturned:
            # Handle rare case of duplicate usernames/emails
            users = User.objects.filter(
                Q(username__iexact=normalized_username) |
                Q(email__iexact=normalized_username)
            ).order_by('date_joined')
            user = users.first()

        # Verify password and check if user is active
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None