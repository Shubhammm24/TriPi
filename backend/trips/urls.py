"""URL routing for the trips app.

URL design:
- /api/generate, /api/refine, /api/chat — match existing FastAPI routes
  so the Next.js frontend works without URL changes.
- /api/tasks/<id>/ — new polling endpoint for async task results.
- /api/extract-places, /api/unsplash — match existing routes.
- /api/sessions/ — new authenticated endpoint for trip history.
- /health — matches existing healthcheck used by Docker and monitoring.
"""

from django.urls import path

from trips.views import (
    ChatView,
    ExtractPlacesView,
    GenerateView,
    HealthView,
    RefineView,
    SessionDetailView,
    SessionListView,
    TaskStatusView,
    UnsplashProxyView,
)

urlpatterns = [
    # Health check
    path("health", HealthView.as_view(), name="health"),

    # Core agent endpoints (async via Celery)
    path("api/generate", GenerateView.as_view(), name="generate"),
    path("api/refine", RefineView.as_view(), name="refine"),
    path("api/chat", ChatView.as_view(), name="chat"),

    # Task polling
    path("api/tasks/<uuid:task_id>/", TaskStatusView.as_view(), name="task-status"),

    # Synchronous utility endpoints
    path("api/extract-places", ExtractPlacesView.as_view(), name="extract-places"),
    path("api/unsplash", UnsplashProxyView.as_view(), name="unsplash"),

    # Session history (authenticated)
    path("api/sessions/", SessionListView.as_view(), name="session-list"),
    path("api/sessions/<uuid:session_id>/", SessionDetailView.as_view(), name="session-detail"),
]
