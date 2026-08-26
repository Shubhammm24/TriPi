"""DRF views for the trips app.

Why APIView instead of ViewSet?
- These endpoints don't map cleanly to CRUD on a single model.
  GenerateView creates 3 models and dispatches a Celery task.
  ViewSets would force awkward overrides of create/list/retrieve.
- APIView makes the logic for each endpoint explicit and linear:
  validate → create models → dispatch → respond.
- In an interview, you can trace exactly what each endpoint does
  without navigating ViewSet mixin inheritance.
"""

import json
import logging
import os
import re

import httpx
from django.conf import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics

from trips.models import AgentTask, Itinerary, Message, Session, TripPreferences
from trips.permissions import IsOwner
from trips.serializers import (
    ChatRequestSerializer,
    ExtractRequestSerializer,
    ExtractResponseSerializer,
    GenerateRequestSerializer,
    ItineraryResponseSerializer,
    RefineRequestSerializer,
    SessionDetailSerializer,
    SessionSerializer,
    TaskCreatedSerializer,
    TaskStatusSerializer,
)
from trips.tasks import run_agent_task

logger = logging.getLogger("trips.views")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


class HealthView(APIView):
    """GET /health — simple liveness probe.

    Matches the existing FastAPI endpoint so Docker healthchecks and
    monitoring don't need reconfiguration.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok", "agent": "TriPi v2.0 (Django)"})


# ---------------------------------------------------------------------------
# Generate / Refine / Chat — async via Celery
# ---------------------------------------------------------------------------


class GenerateView(APIView):
    """POST /api/generate — create a new itinerary from preferences.

    Flow:
    1. Validate the request body
    2. Create Session + TripPreferences in the database
    3. Dispatch a Celery task to run the agent
    4. Return {session_id, task_id, status: "pending"} immediately

    The frontend polls GET /api/tasks/<task_id>/ for the result.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Create session (link to user if authenticated)
        session = Session.objects.create(
            user=request.user if request.user.is_authenticated else None,
        )

        # Persist preferences
        TripPreferences.objects.create(
            session=session,
            budget=data["budget"],
            duration=data["duration"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            origin=data["origin"],
            destination=data["destination"],
            purpose=data.get("purpose", "Leisure"),
            interests=data.get("interests", []),
            dietary_preferences=data.get("dietary_preferences", []),
            mobility_requirements=data.get("mobility_requirements", ""),
            accommodation_type=data.get("accommodation_type", ""),
            walking_tolerance=data.get("walking_tolerance", ""),
            hidden_gems_preference=data.get("hidden_gems_preference", False),
            cuisine_preferences=data.get("cuisine_preferences", []),
            amenities=data.get("amenities", []),
        )

        # Build prompt (same template as FastAPI main.py)
        prompt = f"""Plan a trip with these preferences:
- Destination: {data['destination']}
- Duration: {data['duration']} days
- Dates: {data['start_date']} to {data['end_date']}
- Budget: {data['budget']}
- Traveling from: {data['origin']}
- Purpose: {data.get('purpose', 'Leisure')}
- Interests: {', '.join(data.get('interests', [])) or 'Various'}
- Dietary: {', '.join(data.get('dietary_preferences', [])) or 'No restrictions'}
- Mobility: {data.get('mobility_requirements') or 'No special needs'}
- Accommodation: {data.get('accommodation_type') or 'Any'}
- Walking tolerance: {data.get('walking_tolerance') or 'Moderate'}
- Cuisine preferences: {', '.join(data.get('cuisine_preferences', [])) or 'Local'}
- Hidden gems preference: {'Yes' if data.get('hidden_gems_preference') else 'No'}

Please use your tools to gather real data and then create a detailed day-by-day itinerary."""

        # Create agent task record
        agent_task = AgentTask.objects.create(
            session=session,
            task_type="generate",
        )

        # Dispatch to Celery
        celery_result = run_agent_task.delay(
            task_id=str(agent_task.id),
            session_id=str(session.id),
            prompt=prompt,
            thread_id=str(session.thread_id),
            task_type="generate",
        )

        # Store the Celery task ID for potential revocation
        agent_task.celery_task_id = celery_result.id
        agent_task.save(update_fields=["celery_task_id"])

        return Response(
            TaskCreatedSerializer({
                "session_id": session.id,
                "task_id": agent_task.id,
                "status": "pending",
            }).data,
            status=status.HTTP_202_ACCEPTED,
        )


class RefineView(APIView):
    """POST /api/refine — refine an existing itinerary based on feedback.

    Same async pattern as GenerateView but re-uses an existing session.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefineRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            session = Session.objects.get(id=data["session_id"])
        except Session.DoesNotExist:
            return Response(
                {"detail": "Session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        prompt = f"Please refine the itinerary based on this feedback: {data['feedback']}"

        agent_task = AgentTask.objects.create(
            session=session,
            task_type="refine",
        )

        celery_result = run_agent_task.delay(
            task_id=str(agent_task.id),
            session_id=str(session.id),
            prompt=prompt,
            thread_id=str(session.thread_id),
            task_type="refine",
        )

        agent_task.celery_task_id = celery_result.id
        agent_task.save(update_fields=["celery_task_id"])

        return Response(
            TaskCreatedSerializer({
                "session_id": session.id,
                "task_id": agent_task.id,
                "status": "pending",
            }).data,
            status=status.HTTP_202_ACCEPTED,
        )


class ChatView(APIView):
    """POST /api/chat — free-form conversation with the travel agent."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Get or create session
        try:
            session = Session.objects.get(id=data["session_id"])
        except Session.DoesNotExist:
            session = Session.objects.create(
                id=data["session_id"],
                user=request.user if request.user.is_authenticated else None,
            )

        agent_task = AgentTask.objects.create(
            session=session,
            task_type="chat",
        )

        celery_result = run_agent_task.delay(
            task_id=str(agent_task.id),
            session_id=str(session.id),
            prompt=data["message"],
            thread_id=str(session.thread_id),
            task_type="chat",
        )

        agent_task.celery_task_id = celery_result.id
        agent_task.save(update_fields=["celery_task_id"])

        return Response(
            TaskCreatedSerializer({
                "session_id": session.id,
                "task_id": agent_task.id,
                "status": "pending",
            }).data,
            status=status.HTTP_202_ACCEPTED,
        )


# ---------------------------------------------------------------------------
# Task polling
# ---------------------------------------------------------------------------


class TaskStatusView(APIView):
    """GET /api/tasks/<task_id>/ — poll for async task completion.

    The frontend calls this every 2 seconds after submitting a generate/
    refine/chat request. Returns the task status and, when completed, the
    full itinerary response payload.

    Why a dedicated model + endpoint instead of just using Celery's
    AsyncResult?
    - AsyncResult.get() blocks. We need a non-blocking check.
    - AsyncResult.status only gives you Celery internals (PENDING/STARTED/
      SUCCESS/FAILURE). We want domain-specific statuses.
    - The result is persisted in PostgreSQL, surviving Redis restarts.
    """

    permission_classes = [AllowAny]

    def get(self, request, task_id):
        try:
            agent_task = AgentTask.objects.get(id=task_id)
        except AgentTask.DoesNotExist:
            return Response(
                {"detail": "Task not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            TaskStatusSerializer({
                "task_id": agent_task.id,
                "status": agent_task.status,
                "result": agent_task.result,
                "error": agent_task.error,
            }).data
        )


# ---------------------------------------------------------------------------
# Extract places (synchronous — fast LLM call, ~2s)
# ---------------------------------------------------------------------------

_extract_llm = None


def _get_extract_llm():
    """Lazy-load the extraction LLM (same pattern as FastAPI main.py)."""
    global _extract_llm
    if _extract_llm is None:
        _extract_llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1,
            max_output_tokens=8192,
        )
    return _extract_llm


class ExtractPlacesView(APIView):
    """POST /api/extract-places — extract structured place data from markdown.

    This is kept synchronous (not Celery) because:
    - It's a single fast LLM call (~2 seconds)
    - The frontend needs the result immediately to render the map/budget tabs
    - It doesn't call any external APIs beyond Gemini

    The logic is a direct port from FastAPI's extract_places() endpoint.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ExtractRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        content = ""
        try:
            llm = _get_extract_llm()

            extraction_prompt = f"""Analyze this travel itinerary and extract structured data.

ITINERARY:
{data['itinerary'][:6000]}

DESTINATION: {data['destination']}
USER BUDGET: {data.get('budget', '')}

Return a JSON object with this EXACT structure (no markdown, no code fences, just raw JSON):
{{
  "places": [
    {{
      "name": "Place Name",
      "lat": 35.6762,
      "lon": 139.6503,
      "day": 1,
      "time": "9:00 AM",
      "category": "attraction|restaurant|hotel|transport|shopping|entertainment",
      "cost": 1500,
      "cost_usd": 10,
      "currency": "JPY",
      "description": "Brief description"
    }}
  ],
  "budget_summary": {{
    "total_estimated": 285000,
    "user_budget": 300000,
    "currency": "USD",
    "breakdown": {{
      "accommodation": 120000,
      "food": 45000,
      "activities": 35000,
      "transport": 25000,
      "miscellaneous": 10000
    }}
  }}
}}

IMPORTANT:
- Use REAL latitude/longitude coordinates for each place in {data['destination']}
- Extract ALL places mentioned in the itinerary
- Estimate costs in USD for budget_summary
- Parse the user budget "{data.get('budget', '')}" into a number for user_budget
- Return ONLY valid JSON, no markdown formatting"""

            result = llm.invoke(extraction_prompt)
            content = result.content if hasattr(result, "content") else str(result)

            # Clean up response — strip markdown code fences if present
            content = content.strip()
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

            parsed = json.loads(content)

            places = parsed.get("places", [])
            budget_data = parsed.get("budget_summary", {})
            breakdown = budget_data.get("breakdown", {})

            response_data = {
                "places": places,
                "budget_summary": {
                    "total_estimated": budget_data.get("total_estimated", 0),
                    "user_budget": budget_data.get("user_budget", 0),
                    "currency": budget_data.get("currency", "USD"),
                    "breakdown": {
                        "accommodation": breakdown.get("accommodation", 0),
                        "food": breakdown.get("food", 0),
                        "activities": breakdown.get("activities", 0),
                        "transport": breakdown.get("transport", 0),
                        "miscellaneous": breakdown.get("miscellaneous", 0),
                    },
                },
            }

            return Response(response_data)

        except json.JSONDecodeError as e:
            logger.warning("JSON parse error in extract-places: %s", e)
            logger.debug("Raw content: %s", content[:500])
            return Response({"places": [], "budget_summary": {"total_estimated": 0, "user_budget": 0, "currency": "USD", "breakdown": {"accommodation": 0, "food": 0, "activities": 0, "transport": 0, "miscellaneous": 0}}})
        except Exception:
            logger.exception("Error in /api/extract-places")
            return Response({"places": [], "budget_summary": {"total_estimated": 0, "user_budget": 0, "currency": "USD", "breakdown": {"accommodation": 0, "food": 0, "activities": 0, "transport": 0, "miscellaneous": 0}}})


# ---------------------------------------------------------------------------
# Unsplash proxy
# ---------------------------------------------------------------------------


class UnsplashProxyView(APIView):
    """GET /api/unsplash — proxy Unsplash API to keep access key server-side.

    Direct port from FastAPI. Uses httpx for the outgoing request.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get("query", "")
        per_page = int(request.query_params.get("per_page", 6))
        access_key = os.getenv("UNSPLASH_ACCESS_KEY", "")

        if not access_key:
            return Response({"results": []})

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(
                    "https://api.unsplash.com/search/photos",
                    params={"query": query, "per_page": per_page, "orientation": "landscape"},
                    headers={"Authorization": f"Client-ID {access_key}"},
                )
                resp.raise_for_status()
                data = resp.json()

            results = []
            for photo in data.get("results", []):
                results.append({
                    "id": photo["id"],
                    "url_small": photo["urls"]["small"],
                    "url_regular": photo["urls"]["regular"],
                    "alt": photo.get("alt_description", query),
                    "author": photo["user"]["name"],
                    "author_url": photo["user"]["links"]["html"],
                })

            return Response({"results": results})

        except Exception as e:
            logger.warning("Unsplash proxy error: %s", e)
            return Response({"results": []})


# ---------------------------------------------------------------------------
# Session history (requires authentication)
# ---------------------------------------------------------------------------


class SessionListView(generics.ListAPIView):
    """GET /api/sessions/ — list the authenticated user's past sessions.

    Requires authentication because sessions are user-scoped.
    Unauthenticated users don't have persistent session history.

    N+1 prevention:
    - select_related('user') avoids a separate query per session to fetch
      the user object. Without it, serializing 50 sessions would fire 51
      queries (1 for sessions + 50 for users). With it: 1 query with a JOIN.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = SessionSerializer

    def get_queryset(self):
        return (
            Session.objects
            .filter(user=self.request.user)
            .select_related("user")
        )


class SessionDetailView(APIView):
    """GET /api/sessions/<id>/ — get a session with all its data.

    Permission: IsAuthenticated + IsOwner (belt AND suspenders).
    - IsAuthenticated: rejects unauthenticated requests (401).
    - IsOwner: rejects requests from users who don't own this session (403).
    - Queryset filter(user=...): prevents listing other users' data.

    N+1 prevention:
    - prefetch_related('itineraries', 'messages') batches the related
      queries. Without it, serializing a session with 5 itineraries and
      20 messages would fire 3 queries (1 session + 1 itineraries + 1
      messages) vs 1 + 5 + 20 = 26 queries.
    """

    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request, session_id):
        try:
            session = (
                Session.objects
                .select_related("preferences")
                .prefetch_related("itineraries", "messages")
                .get(id=session_id, user=request.user)
            )
        except Session.DoesNotExist:
            return Response(
                {"detail": "Session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Object-level permission check
        self.check_object_permissions(request, session)

        serializer = SessionDetailSerializer(session)
        return Response(serializer.data)
