"""Django admin registration for the accounts app."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Use Django's built-in UserAdmin — it handles password hashing,
    permissions UI, and search out of the box."""

    pass
