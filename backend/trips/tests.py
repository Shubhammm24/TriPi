"""Tests for the trips app.

Uses pytest-django. Mock the LLM — do not make real API calls in tests.

Run with:
    PYTHONPATH=d:\Projects\Travel_Agent-main\backend;d:\Projects\Travel_Agent-main
    py -3 -m pytest backend/trips/tests.py -v --settings=tripi_project.settings

Coverage:
    1. Trip creation via POST /api/generate
    2. Permission scoping (User A cannot read User B's session)
    3. Serializer validation failures (missing required fields)
    4. Task status polling
    5. Health endpoint
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from trips.models import AgentTask, Itinerary, Message, Session, TripPreferences
from trips.serializers import GenerateRequestSerializer, RefineRequestSerializer

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_a(db):
    return User.objects.create_user(username="alice", password="testpass123")


@pytest.fixture
def user_b(db):
    return User.objects.create_user(username="bob", password="testpass456")


@pytest.fixture
def alice_client(user_a):
    client = APIClient()
    client.force_authenticate(user=user_a)
    return client


@pytest.fixture
def bob_client(user_b):
    client = APIClient()
    client.force_authenticate(user=user_b)
    return client


@pytest.fixture
def alice_session(user_a):
    """Create a session with preferences and an itinerary for user A."""
    session = Session.objects.create(user=user_a, status=Session.Status.COMPLETED)
    TripPreferences.objects.create(
        session=session,
        budget="$2000",
        duration=5,
        start_date="2026-01-10",
        end_date="2026-01-15",
        origin="New York",
        destination="Tokyo",
    )
    Itinerary.objects.create(
        session=session,
        version=1,
        content="# Day 1\nVisit Shibuya crossing...",
        tool_calls=["weather_lookup", "places_search"],
    )
    Message.objects.create(
        session=session,
        role=Message.Role.USER,
        content="Plan a 5-day trip to Tokyo",
    )
    Message.objects.create(
        session=session,
        role=Message.Role.ASSISTANT,
        content="# Day 1\nVisit Shibuya crossing...",
    )
    return session


# ---------------------------------------------------------------------------
# Test: Health endpoint
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_returns_ok(self, api_client, db):
        response = api_client.get("/health")
        assert response.status_code == 200
        assert response.data["status"] == "ok"


# ---------------------------------------------------------------------------
# Test: Trip creation via POST /api/generate
# ---------------------------------------------------------------------------

class TestGenerateEndpoint:
    """Tests for POST /api/generate.

    We mock the Celery task so no real agent/LLM calls are made.
    """

    @patch("trips.views.run_agent_task.delay")
    def test_generate_creates_session_and_returns_202(self, mock_delay, api_client, db):
        """Successful generation creates Session + TripPreferences + AgentTask
        and returns 202 with task_id and session_id."""
        mock_delay.return_value = MagicMock(id="celery-task-id-123")

        payload = {
            "destination": "Tokyo",
            "origin": "New York",
            "start_date": "2026-01-10",
            "end_date": "2026-01-15",
            "budget": "$2000",
            "duration": 5,
            "purpose": "Leisure",
            "interests": ["food", "culture"],
        }

        response = api_client.post("/api/generate", payload, format="json")

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert "session_id" in response.data
        assert "task_id" in response.data
        assert response.data["status"] == "pending"

        # Verify database records were created
        session_id = response.data["session_id"]
        session = Session.objects.get(id=session_id)
        assert session.status == Session.Status.PENDING

        prefs = TripPreferences.objects.get(session=session)
        assert prefs.destination == "Tokyo"
        assert prefs.duration == 5

        task = AgentTask.objects.get(session=session)
        assert task.task_type == "generate"

        # Verify Celery task was dispatched
        mock_delay.assert_called_once()

    def test_generate_rejects_missing_fields(self, api_client, db):
        """Missing required fields should return 400, not 500."""
        response = api_client.post("/api/generate", {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Test: Permission scoping (User A cannot read User B's data)
# ---------------------------------------------------------------------------

class TestPermissionScoping:
    """Verify that users cannot access each other's sessions.

    This tests both queryset filtering AND object-level permissions.
    """

    def test_alice_can_see_her_sessions(self, alice_client, alice_session):
        """Alice should see her own sessions."""
        response = alice_client.get("/api/sessions/")
        assert response.status_code == 200
        # Pagination wraps results
        results = response.data.get("results", response.data)
        session_ids = [s["id"] for s in results]
        assert str(alice_session.id) in session_ids

    def test_bob_cannot_see_alice_sessions(self, bob_client, alice_session):
        """Bob should NOT see Alice's sessions in the list."""
        response = bob_client.get("/api/sessions/")
        assert response.status_code == 200
        results = response.data.get("results", response.data)
        session_ids = [s["id"] for s in results]
        assert str(alice_session.id) not in session_ids

    def test_bob_cannot_access_alice_session_detail(self, bob_client, alice_session):
        """Bob should get 404 when accessing Alice's session by ID.

        Why 404 and not 403? The queryset filter(user=request.user) means
        the session is never even loaded for Bob. From Bob's perspective,
        it doesn't exist. This is more secure than 403 which confirms
        the resource exists.
        """
        response = bob_client.get(f"/api/sessions/{alice_session.id}/")
        assert response.status_code == 404

    def test_unauthenticated_cannot_access_sessions(self, api_client, alice_session):
        """Unauthenticated users should get 401 on the sessions list."""
        response = api_client.get("/api/sessions/")
        assert response.status_code == 401

    def test_alice_can_access_her_session_detail(self, alice_client, alice_session):
        """Alice should be able to access her own session's detail view."""
        response = alice_client.get(f"/api/sessions/{alice_session.id}/")
        assert response.status_code == 200
        assert response.data["id"] == str(alice_session.id)
        assert response.data["status"] == "completed"
        # Should include nested data
        assert "preferences" in response.data
        assert "itineraries" in response.data
        assert "messages" in response.data


# ---------------------------------------------------------------------------
# Test: Serializer validation
# ---------------------------------------------------------------------------

class TestSerializerValidation:
    """Test that serializers reject invalid input properly."""

    def test_generate_serializer_missing_required_fields(self):
        """GenerateRequestSerializer should fail when required fields are missing."""
        serializer = GenerateRequestSerializer(data={})
        assert not serializer.is_valid()
        # These fields are required
        assert "budget" in serializer.errors
        assert "duration" in serializer.errors
        assert "destination" in serializer.errors

    def test_generate_serializer_valid_input(self):
        """GenerateRequestSerializer should accept valid input."""
        serializer = GenerateRequestSerializer(data={
            "budget": "$1500",
            "duration": 3,
            "start_date": "2026-03-01",
            "end_date": "2026-03-04",
            "origin": "London",
            "destination": "Paris",
        })
        assert serializer.is_valid(), serializer.errors

    def test_generate_serializer_rejects_negative_duration(self):
        """Duration must be >= 1."""
        serializer = GenerateRequestSerializer(data={
            "budget": "$1500",
            "duration": 0,
            "start_date": "2026-03-01",
            "end_date": "2026-03-04",
            "origin": "London",
            "destination": "Paris",
        })
        assert not serializer.is_valid()
        assert "duration" in serializer.errors

    def test_refine_serializer_requires_session_id(self):
        """RefineRequestSerializer needs a valid UUID session_id."""
        serializer = RefineRequestSerializer(data={"feedback": "Add more food"})
        assert not serializer.is_valid()
        assert "session_id" in serializer.errors

    def test_refine_serializer_valid(self):
        serializer = RefineRequestSerializer(data={
            "session_id": str(uuid.uuid4()),
            "feedback": "Add more food recommendations",
        })
        assert serializer.is_valid(), serializer.errors


# ---------------------------------------------------------------------------
# Test: Task status polling
# ---------------------------------------------------------------------------

class TestTaskStatusEndpoint:
    def test_task_not_found_returns_404(self, api_client, db):
        fake_id = str(uuid.uuid4())
        response = api_client.get(f"/api/tasks/{fake_id}/")
        assert response.status_code == 404

    def test_pending_task_returns_status(self, api_client, db):
        session = Session.objects.create()
        task = AgentTask.objects.create(session=session, task_type="generate")

        response = api_client.get(f"/api/tasks/{task.id}/")
        assert response.status_code == 200
        assert response.data["status"] == "pending"
        assert response.data["result"] is None

    def test_completed_task_returns_result(self, api_client, db):
        session = Session.objects.create()
        task = AgentTask.objects.create(
            session=session,
            task_type="generate",
            status=AgentTask.Status.COMPLETED,
            result={
                "session_id": str(session.id),
                "itinerary": "# Your Trip\nDay 1...",
                "tool_calls": ["weather_lookup"],
                "error": None,
            },
        )

        response = api_client.get(f"/api/tasks/{task.id}/")
        assert response.status_code == 200
        assert response.data["status"] == "completed"
        assert response.data["result"]["itinerary"] == "# Your Trip\nDay 1..."


# ---------------------------------------------------------------------------
# Test: Model constraints
# ---------------------------------------------------------------------------

class TestModelConstraints:
    def test_itinerary_version_unique_per_session(self, db):
        """Two itineraries with the same version in the same session should fail."""
        session = Session.objects.create()
        Itinerary.objects.create(session=session, version=1, content="v1")

        with pytest.raises(Exception):
            Itinerary.objects.create(session=session, version=1, content="v1 duplicate")

    def test_itinerary_version_unique_across_sessions(self, db):
        """Same version number in different sessions should be fine."""
        session1 = Session.objects.create()
        session2 = Session.objects.create()
        Itinerary.objects.create(session=session1, version=1, content="s1v1")
        Itinerary.objects.create(session=session2, version=1, content="s2v1")
        # No exception — this should work


# ---------------------------------------------------------------------------
# Test: Message model
# ---------------------------------------------------------------------------

class TestMessageModel:
    def test_messages_ordered_by_created_at(self, alice_session):
        """Messages should be ordered chronologically."""
        messages = list(alice_session.messages.all())
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"
        assert messages[0].created_at <= messages[1].created_at
