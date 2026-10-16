"""DRF serializers for the trips app.

These replace the Pydantic BaseModel schemas from the FastAPI main.py.

Why DRF serializers instead of keeping Pydantic?
- DRF serializers integrate with Django's ORM: calling .save() on a
  ModelSerializer creates or updates the corresponding model instance.
- They plug into DRF's content negotiation, validation errors, and
  browsable API.
- The Pydantic models in agent/state.py remain untouched — they serve the
  agent's internal state, not the HTTP API.
"""

from rest_framework import serializers

from trips.models import AgentTask, Itinerary, Message, Session, TripPreferences


# ---------------------------------------------------------------------------
# Request serializers — validate incoming POST bodies
# ---------------------------------------------------------------------------


class GenerateRequestSerializer(serializers.Serializer):
    """Validates POST /api/generate — identical fields to the old GenerateRequest."""

    budget = serializers.CharField()
    duration = serializers.IntegerField(min_value=1)
    start_date = serializers.CharField()
    end_date = serializers.CharField()
    origin = serializers.CharField()
    destination = serializers.CharField()
    purpose = serializers.CharField(default="Leisure")
    interests = serializers.ListField(child=serializers.CharField(), default=list)
    dietary_preferences = serializers.ListField(
        child=serializers.CharField(), default=list
    )
    mobility_requirements = serializers.CharField(
        required=False, default="", allow_blank=True
    )
    accommodation_type = serializers.CharField(
        required=False, default="", allow_blank=True
    )
    walking_tolerance = serializers.CharField(
        required=False, default="", allow_blank=True
    )
    hidden_gems_preference = serializers.BooleanField(default=False)
    cuisine_preferences = serializers.ListField(
        child=serializers.CharField(), default=list
    )
    amenities = serializers.ListField(child=serializers.CharField(), default=list)


class RefineRequestSerializer(serializers.Serializer):
    """Validates POST /api/refine."""

    session_id = serializers.UUIDField()
    feedback = serializers.CharField()


class ChatRequestSerializer(serializers.Serializer):
    """Validates POST /api/chat."""

    session_id = serializers.UUIDField(required=False, allow_null=True)
    message = serializers.CharField()


class ExtractRequestSerializer(serializers.Serializer):
    """Validates POST /api/extract-places."""

    itinerary = serializers.CharField()
    destination = serializers.CharField()
    budget = serializers.CharField(default="", allow_blank=True)


# ---------------------------------------------------------------------------
# Response serializers — shape outgoing JSON
# ---------------------------------------------------------------------------


class TaskCreatedSerializer(serializers.Serializer):
    """Response for generate/refine/chat — returns IDs for polling."""

    session_id = serializers.UUIDField()
    task_id = serializers.UUIDField()
    status = serializers.CharField(default="pending")


class ItineraryResponseSerializer(serializers.Serializer):
    """The final itinerary payload — same shape as the old FastAPI response.

    This is what TaskStatusView returns inside result when status=completed.
    """

    session_id = serializers.UUIDField()
    itinerary = serializers.CharField()
    tool_calls = serializers.ListField(child=serializers.CharField(), default=list)
    error = serializers.CharField(default=None, allow_null=True, allow_blank=True)


class TaskStatusSerializer(serializers.Serializer):
    """Response for GET /api/tasks/<id>/ — polling endpoint."""

    task_id = serializers.UUIDField()
    status = serializers.CharField()
    result = ItineraryResponseSerializer(allow_null=True)
    error = serializers.CharField(default="", allow_blank=True)


# ---------------------------------------------------------------------------
# Extract-places response serializers
# ---------------------------------------------------------------------------


class PlaceItemSerializer(serializers.Serializer):
    name = serializers.CharField(default="")
    lat = serializers.FloatField(default=0.0)
    lon = serializers.FloatField(default=0.0)
    day = serializers.IntegerField(default=1)
    time = serializers.CharField(default="")
    category = serializers.CharField(default="attraction")
    cost = serializers.FloatField(default=0.0)
    cost_usd = serializers.FloatField(default=0.0)
    currency = serializers.CharField(default="USD")
    description = serializers.CharField(default="")


class BudgetBreakdownSerializer(serializers.Serializer):
    accommodation = serializers.FloatField(default=0.0)
    food = serializers.FloatField(default=0.0)
    activities = serializers.FloatField(default=0.0)
    transport = serializers.FloatField(default=0.0)
    miscellaneous = serializers.FloatField(default=0.0)


class BudgetSummarySerializer(serializers.Serializer):
    total_estimated = serializers.FloatField(default=0.0)
    user_budget = serializers.FloatField(default=0.0)
    currency = serializers.CharField(default="USD")
    breakdown = BudgetBreakdownSerializer()


class ExtractResponseSerializer(serializers.Serializer):
    places = PlaceItemSerializer(many=True, default=list)
    budget_summary = BudgetSummarySerializer()


# ---------------------------------------------------------------------------
# Model serializers — for history/listing endpoints
# ---------------------------------------------------------------------------


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ["id", "thread_id", "status", "created_at", "last_active"]


class TripPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripPreferences
        exclude = ["session"]


class ItinerarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Itinerary
        fields = ["id", "version", "content", "structured_data", "tool_calls", "created_at"]


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for conversation turns."""

    class Meta:
        model = Message
        fields = ["id", "role", "content", "created_at"]
        read_only_fields = ["id", "created_at"]


class SessionDetailSerializer(serializers.ModelSerializer):
    """Session with nested preferences, itineraries, and messages — for detail views."""

    preferences = TripPreferencesSerializer(read_only=True)
    itineraries = ItinerarySerializer(many=True, read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Session
        fields = [
            "id", "thread_id", "status", "created_at", "last_active",
            "preferences", "itineraries", "messages",
        ]
