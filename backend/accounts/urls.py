"""URL routing for the accounts app.

Endpoints:
    POST /api/auth/register/       — create a new user
    POST /api/auth/token/          — obtain JWT access + refresh tokens
    POST /api/auth/token/refresh/  — refresh an expired access token

Why JWT via simplejwt?
- The frontend is a separate Next.js app on a different port/domain.
- Session cookies require same-origin or complex CORS + SameSite config.
- JWT Authorization: Bearer headers work cleanly cross-origin with zero
  cookie configuration.
"""

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from accounts.views import RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("token/", TokenObtainPairView.as_view(), name="token-obtain"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]
