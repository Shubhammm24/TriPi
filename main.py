"""FastAPI backend for the TriPi AI Travel Planner.

Run with:
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import os
import re
import json
import uuid
import traceback
from datetime import datetime
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

load_dotenv()

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="TriPi — AI Travel Planner API",
    description="Agentic travel planning powered by LangGraph + Gemini",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build agent once at startup
api_key = os.getenv("GOOGLE_API_KEY", "")
if not api_key:
    raise RuntimeError("GOOGLE_API_KEY not set in environment / .env file")

# Lazy agent build — delay until first request to avoid import errors at startup
_agent = None


def get_agent():
    global _agent
    if _agent is None:
        from agent.graph import build_agent
        _agent = build_agent(api_key)
    return _agent


# In-memory session store (maps session_id → thread_id for LangGraph memory)
sessions: dict[str, str] = {}

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class GenerateRequest(BaseModel):
    """Request body for itinerary generation."""

    budget: str
    duration: int
    start_date: str
    end_date: str
    origin: str
    destination: str
    purpose: str = "Leisure"
    interests: list[str] = Field(default_factory=list)
    dietary_preferences: list[str] = Field(default_factory=list)
    mobility_requirements: Optional[str] = None
    accommodation_type: Optional[str] = None
    walking_tolerance: Optional[str] = None
    hidden_gems_preference: bool = False
    cuisine_preferences: list[str] = Field(default_factory=list)
    amenities: list[str] = Field(default_factory=list)


class RefineRequest(BaseModel):
    """Request body for itinerary refinement."""

    session_id: str
    feedback: str


class ChatRequest(BaseModel):
    """Request body for free-form chat."""

    session_id: str
    message: str


class ItineraryResponse(BaseModel):
    """Response body returned by generation/refinement."""

    session_id: str
    itinerary: str
    tool_calls: list[str] = Field(default_factory=list)
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _invoke_agent(message: str, thread_id: str) -> tuple[str, list[str]]:
    """Run the agent with a human message and return (response, tool_names)."""
    agent = get_agent()
    config = {"configurable": {"thread_id": thread_id}}

    print(f"\n{'='*60}")
    print(f"[TriPi] Invoking agent with thread: {thread_id}")
    print(f"[TriPi] Prompt: {message[:200]}...")
    print(f"{'='*60}\n")

    result = agent.invoke({"messages": [HumanMessage(content=message)]}, config)

    # Extract final AI message
    messages = result.get("messages", [])
    ai_response = ""
    tool_names: list[str] = []

    print(f"[TriPi] Got {len(messages)} messages back from agent")

    for msg in messages:
        msg_type = getattr(msg, "type", None)
        if msg_type == "ai":
            content = getattr(msg, "content", "")
            if isinstance(content, str) and content.strip():
                ai_response = content
            elif isinstance(content, list):
                # Some models return content as list of parts
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                    elif isinstance(part, str):
                        text_parts.append(part)
                joined = "\n".join(text_parts).strip()
                if joined:
                    ai_response = joined
        elif msg_type == "tool":
            name = getattr(msg, "name", None)
            if name:
                tool_names.append(name)

    print(f"[TriPi] Tools used: {tool_names}")
    print(f"[TriPi] Response length: {len(ai_response)} chars")
    if not ai_response:
        print(f"[TriPi] WARNING: Empty response! Raw messages:")
        for i, m in enumerate(messages):
            print(f"  [{i}] type={getattr(m, 'type', '?')} content_type={type(getattr(m, 'content', None)).__name__} content_preview={str(getattr(m, 'content', ''))[:100]}")

    return ai_response, tool_names


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "agent": "TriPi v2.0"}


@app.post("/api/generate", response_model=ItineraryResponse)
async def generate_itinerary(req: GenerateRequest):
    """Generate a new travel itinerary from preferences."""
    session_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())
    sessions[session_id] = thread_id

    # Build a structured prompt from preferences
    prompt = f"""Plan a trip with these preferences:
- Destination: {req.destination}
- Duration: {req.duration} days
- Dates: {req.start_date} to {req.end_date}
- Budget: {req.budget}
- Traveling from: {req.origin}
- Purpose: {req.purpose}
- Interests: {', '.join(req.interests) if req.interests else 'Various'}
- Dietary: {', '.join(req.dietary_preferences) if req.dietary_preferences else 'No restrictions'}
- Mobility: {req.mobility_requirements or 'No special needs'}
- Accommodation: {req.accommodation_type or 'Any'}
- Walking tolerance: {req.walking_tolerance or 'Moderate'}
- Cuisine preferences: {', '.join(req.cuisine_preferences) if req.cuisine_preferences else 'Local'}
- Hidden gems preference: {'Yes' if req.hidden_gems_preference else 'No'}

Please use your tools to gather real data and then create a detailed day-by-day itinerary."""

    try:
        itinerary, tools_used = _invoke_agent(prompt, thread_id)

        if not itinerary:
            itinerary = "The agent did not return an itinerary. This may be a temporary issue. Please try again."

        return ItineraryResponse(
            session_id=session_id,
            itinerary=itinerary,
            tool_calls=tools_used,
        )
    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"\n[TriPi] ERROR in /api/generate:\n{error_detail}")
        return ItineraryResponse(
            session_id=session_id,
            itinerary=f"## ⚠️ Error Generating Itinerary\n\nSomething went wrong: **{str(e)}**\n\nPlease check that your `GOOGLE_API_KEY` is valid in the `.env` file and try again.",
            tool_calls=[],
            error=str(e),
        )


@app.post("/api/refine", response_model=ItineraryResponse)
async def refine_itinerary(req: RefineRequest):
    """Refine an existing itinerary based on user feedback."""
    thread_id = sessions.get(req.session_id)
    if not thread_id:
        raise HTTPException(status_code=404, detail="Session not found")

    prompt = f"Please refine the itinerary based on this feedback: {req.feedback}"

    try:
        itinerary, tools_used = _invoke_agent(prompt, thread_id)
        return ItineraryResponse(
            session_id=req.session_id,
            itinerary=itinerary or "No changes were made. Please provide more specific feedback.",
            tool_calls=tools_used,
        )
    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"\n[TriPi] ERROR in /api/refine:\n{error_detail}")
        return ItineraryResponse(
            session_id=req.session_id,
            itinerary=f"## ⚠️ Error Refining\n\n{str(e)}",
            tool_calls=[],
            error=str(e),
        )


@app.post("/api/chat", response_model=ItineraryResponse)
async def chat(req: ChatRequest):
    """Free-form chat with the travel agent."""
    thread_id = sessions.get(req.session_id)
    if not thread_id:
        thread_id = str(uuid.uuid4())
        sessions[req.session_id] = thread_id

    try:
        response, tools_used = _invoke_agent(req.message, thread_id)
        return ItineraryResponse(
            session_id=req.session_id,
            itinerary=response or "I didn't generate a response. Please try again.",
            tool_calls=tools_used,
        )
    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"\n[TriPi] ERROR in /api/chat:\n{error_detail}")
        return ItineraryResponse(
            session_id=req.session_id,
            itinerary=f"## ⚠️ Error\n\n{str(e)}",
            tool_calls=[],
            error=str(e),
        )


# ---------------------------------------------------------------------------
# Structured data extraction (powers Map + Budget)
# ---------------------------------------------------------------------------


class ExtractRequest(BaseModel):
    """Request body for extracting structured places from an itinerary."""

    itinerary: str
    destination: str
    budget: str = ""


class PlaceItem(BaseModel):
    name: str = ""
    lat: float = 0.0
    lon: float = 0.0
    day: int = 1
    time: str = ""
    category: str = "attraction"
    cost: float = 0.0
    cost_usd: float = 0.0
    currency: str = "USD"
    description: str = ""


class BudgetBreakdown(BaseModel):
    accommodation: float = 0.0
    food: float = 0.0
    activities: float = 0.0
    transport: float = 0.0
    miscellaneous: float = 0.0


class BudgetSummary(BaseModel):
    total_estimated: float = 0.0
    user_budget: float = 0.0
    currency: str = "USD"
    breakdown: BudgetBreakdown = Field(default_factory=BudgetBreakdown)


class ExtractResponse(BaseModel):
    places: list[PlaceItem] = Field(default_factory=list)
    budget_summary: BudgetSummary = Field(default_factory=BudgetSummary)


_extract_llm = None


def _get_extract_llm():
    global _extract_llm
    if _extract_llm is None:
        from langchain_google_genai import ChatGoogleGenerativeAI

        _extract_llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash",
            google_api_key=api_key,
            temperature=0.1,
            max_output_tokens=8192,
        )
    return _extract_llm


@app.post("/api/extract-places", response_model=ExtractResponse)
async def extract_places(req: ExtractRequest):
    """Extract structured place data from a markdown itinerary using Gemini."""
    try:
        llm = _get_extract_llm()

        extraction_prompt = f"""Analyze this travel itinerary and extract structured data.

ITINERARY:
{req.itinerary[:6000]}

DESTINATION: {req.destination}
USER BUDGET: {req.budget}

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
- Use REAL latitude/longitude coordinates for each place in {req.destination}
- Extract ALL places mentioned in the itinerary
- Estimate costs in USD for budget_summary
- Parse the user budget "{req.budget}" into a number for user_budget
- Return ONLY valid JSON, no markdown formatting"""

        result = llm.invoke(extraction_prompt)
        content = result.content if hasattr(result, "content") else str(result)

        # Clean up response — strip markdown code fences if present
        content = content.strip()
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

        data = json.loads(content)

        places = [PlaceItem(**p) for p in data.get("places", [])]
        budget_data = data.get("budget_summary", {})
        breakdown = BudgetBreakdown(**budget_data.get("breakdown", {}))
        budget_summary = BudgetSummary(
            total_estimated=budget_data.get("total_estimated", 0),
            user_budget=budget_data.get("user_budget", 0),
            currency=budget_data.get("currency", "USD"),
            breakdown=breakdown,
        )

        return ExtractResponse(places=places, budget_summary=budget_summary)

    except json.JSONDecodeError as e:
        print(f"[TriPi] JSON parse error in extract-places: {e}")
        print(f"[TriPi] Raw content: {content[:500]}")
        return ExtractResponse()
    except Exception as e:
        print(f"[TriPi] ERROR in /api/extract-places: {traceback.format_exc()}")
        return ExtractResponse()


# ---------------------------------------------------------------------------
# Unsplash image proxy (avoids exposing API key to frontend)
# ---------------------------------------------------------------------------


@app.get("/api/unsplash")
async def unsplash_proxy(query: str, per_page: int = 6):
    """Proxy Unsplash API requests to keep the access key server-side."""
    access_key = os.getenv("UNSPLASH_ACCESS_KEY", "")
    if not access_key:
        # Return empty results gracefully — photos are optional
        return {"results": []}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.unsplash.com/search/photos",
                params={"query": query, "per_page": per_page, "orientation": "landscape"},
                headers={"Authorization": f"Client-ID {access_key}"},
            )
            resp.raise_for_status()
            data = resp.json()

        # Return simplified results
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

        return {"results": results}

    except Exception as e:
        print(f"[TriPi] Unsplash proxy error: {e}")
        return {"results": []}

