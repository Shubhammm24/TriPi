"""DRF serializers for user registration and profile."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Validates POST /api/auth/register/ — creates a new user account.

    Password is write-only: it appears in the request but never in responses.
    Uses Django's set_password() to hash the password properly.
    """

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    """Read-only user representation returned after registration or in profile."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "date_joined"]
        read_only_fields = fields
