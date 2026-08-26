"""Database models for the trips app.

Five models, each with a clear reason to exist:

Session
    Replaces the in-memory ``sessions: dict[str, str]`` from FastAPI.
    Now survives restarts because it lives in PostgreSQL. Has a ``status``
    field tracking the overall trip lifecycle.

TripPreferences
    Persists the user's form input. Without this, once the agent finishes
    you lose the original request — no trip history, no re-generation.

Itinerary
    Stores every version of the generated/refined itinerary for a session.
    Versioning lets users revert or diff changes after refinement.
    Includes a ``structured_data`` JSONField for day-by-day machine-readable data.

Message
    Conversation turns for the refine/chat flows, linked to a Session.
    Persists the dialogue so it survives restarts and can be replayed in the UI.
    LangGraph's MemorySaver is in-memory only — this is the durable copy.

AgentTask
    Tracks Celery background jobs. Decouples the HTTP response from the
    30-60 second agent run. Includes duration and token usage for audit.
"""

import uuid

from django.conf import settings
from django.db import models


class Session(models.Model):
    """A planning session — maps a user-facing session_id to an agent thread_id.

    Why UUID primary key?
    - The frontend already expects session_id to be a UUID string.
    - Avoids sequential integer IDs leaking business information
      (competitor can't estimate your volume by incrementing IDs).

    Why a status field here AND on AgentTask?
    - Session.status is the *trip-level* lifecycle: "is this trip done?"
    - AgentTask.status is the *job-level* lifecycle: "did this specific
      Celery task succeed?" A session may have multiple tasks (generate,
      then refine, then chat) — each with its own status.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread_id = models.UUIDField(
        default=uuid.uuid4,
        help_text="LangGraph MemorySaver thread_id — identifies the conversation.",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
        help_text="Nullable so unauthenticated users can still create sessions.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        help_text="Overall trip lifecycle status.",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    last_active = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_active"]

    def __str__(self):
        return f"Session {self.id} [{self.status}]"


class TripPreferences(models.Model):
    """Persisted snapshot of the user's planning form input.

    Fields mirror GenerateRequest from the original FastAPI main.py.
    Stored as individual columns (not a single JSONField) so you can query
    and filter on them — e.g. "show me all trips to Japan".
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField(
        Session,
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    budget = models.CharField(max_length=100)
    duration = models.PositiveIntegerField()
    start_date = models.CharField(max_length=30)
    end_date = models.CharField(max_length=30)
    origin = models.CharField(max_length=200, db_index=True)
    destination = models.CharField(max_length=200, db_index=True)
    purpose = models.CharField(max_length=50, default="Leisure")
    interests = models.JSONField(default=list, blank=True)
    dietary_preferences = models.JSONField(default=list, blank=True)
    mobility_requirements = models.CharField(max_length=200, blank=True, default="")
    accommodation_type = models.CharField(max_length=100, blank=True, default="")
    walking_tolerance = models.CharField(max_length=50, blank=True, default="")
    hidden_gems_preference = models.BooleanField(default=False)
    cuisine_preferences = models.JSONField(default=list, blank=True)
    amenities = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name_plural = "Trip preferences"

    def __str__(self):
        return f"{self.origin} → {self.destination} ({self.duration}d)"


class Itinerary(models.Model):
    """A generated or refined itinerary.

    Why version numbering?
    - Each refinement creates a new Itinerary row (version N+1) instead of
      overwriting. This gives you full history and the ability to revert.
    - tool_calls is a JSONField because the list of tool names doesn't need
      relational querying — it's purely informational.

    Why structured_data?
    - ``content`` is the markdown itinerary for human reading.
    - ``structured_data`` is the machine-readable JSON (day-by-day activities,
      coordinates, costs) for the Map/Budget/Photos tabs. Without it, the
      frontend must call /api/extract-places every time — an LLM round-trip
      that should be cached.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="itineraries",
    )
    version = models.PositiveIntegerField(default=1)
    content = models.TextField(
        help_text="Markdown itinerary content returned by the agent.",
    )
    structured_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Machine-readable day-by-day itinerary data (places, costs, coordinates).",
    )
    tool_calls = models.JSONField(
        default=list,
        blank=True,
        help_text="List of tool names invoked during this generation.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version"]
        verbose_name_plural = "Itineraries"
        constraints = [
            models.UniqueConstraint(
                fields=["session", "version"],
                name="unique_session_version",
            ),
        ]

    def __str__(self):
        return f"Itinerary v{self.version} for {self.session_id}"


class Message(models.Model):
    """A single conversation turn in a refine/chat flow.

    Why this model exists:
    - LangGraph's MemorySaver stores conversation history in-memory.
      When the server restarts, all conversation context is lost.
    - This model is the durable copy — it lets you replay past
      conversations and show chat history in the UI.
    - Linked to Session (not Itinerary) because a conversation may
      span multiple refinements.

    Why not store messages inside Itinerary as a JSONField?
    - Individual rows are queryable: "show me all user messages across
      all sessions that mention 'vegetarian'" for analytics.
    - Timestamps on each message enable "time to first response" metrics.
    """

    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        db_index=True,
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        preview = self.content[:60] + "…" if len(self.content) > 60 else self.content
        return f"[{self.role}] {preview}"


class AgentTask(models.Model):
    """Tracks a Celery background job running the LangGraph agent.

    Why a separate model instead of just using Celery's result backend?
    - Celery results are opaque key-value pairs in Redis. We need to:
      1. Query tasks by session (show all tasks for a session)
      2. Expose a clean REST API response shape
      3. Persist task metadata beyond Redis's default TTL

    Why duration_seconds and tokens_used?
    - Audit trail: "this run took 42s and used 3200 tokens."
    - Cost tracking: multiply tokens_used by per-token price.
    - Performance monitoring: detect regressions in agent speed.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    celery_task_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="The Celery AsyncResult ID for monitoring/revoking.",
    )
    task_type = models.CharField(
        max_length=20,
        choices=[
            ("generate", "Generate"),
            ("refine", "Refine"),
            ("chat", "Chat"),
        ],
        default="generate",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    result = models.JSONField(
        null=True,
        blank=True,
        help_text="The full ItineraryResponse payload once completed.",
    )
    error = models.TextField(
        blank=True,
        default="",
    )
    tools_used = models.JSONField(
        default=list,
        blank=True,
        help_text="Ordered list of tool names called during this run.",
    )
    duration_seconds = models.FloatField(
        null=True,
        blank=True,
        help_text="Wall-clock duration of the agent run in seconds.",
    )
    tokens_used = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Total tokens consumed (prompt + completion) if available.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Task {self.id} [{self.status}] for {self.session_id}"
