"""Custom user model for TriPi.

Why extend AbstractUser even though we don't add custom fields yet?

Django's official documentation explicitly warns:
    "If you're starting a new project, it's highly recommended to set up
    a custom user model, even if the default User model is sufficient."

The reason: changing AUTH_USER_MODEL after running initial migrations
requires resetting ALL migrations in ALL apps (including third-party).
Setting it up now — even as a no-op subclass — is a 2-minute task that
prevents a multi-hour migration nightmare later.
"""

from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """Custom user model — currently identical to Django's default User.

    Extend this later to add fields like:
    - preferred_currency
    - default_origin_city
    - notification_preferences
    """

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username
