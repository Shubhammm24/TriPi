"""Views for user registration.

Token obtain/refresh is handled by simplejwt's built-in views —
we only need a custom view for registration.
"""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import RegisterSerializer, UserSerializer


class RegisterView(APIView):
    """POST /api/auth/register/ — create a new user account.

    Returns the created user's info (no password).
    The frontend should then call POST /api/auth/token/ to get a JWT.

    Why not return the token directly?
    - Separation of concerns: registration and authentication are distinct.
    - The frontend's token management code has one clear entry point.
    - If you later add email verification, registration doesn't grant
      immediate access.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )
