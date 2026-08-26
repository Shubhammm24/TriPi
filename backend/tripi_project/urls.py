"""Root URL configuration for the TriPi Django project.

Maps:
    /admin/          → Django admin site
    /api/auth/       → accounts app (register, token, refresh)
    /api/            → trips app (generate, refine, chat, tasks, etc.)
    /health          → health check (included in trips urls)

Why this structure?
- /api/ prefix matches the existing FastAPI routes so the Next.js frontend
  keeps working without URL changes.
- /admin/ gives you a free dashboard for inspecting data — one of Django's
  biggest advantages over FastAPI.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("", include("trips.urls")),
]
