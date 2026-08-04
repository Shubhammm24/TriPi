"""FastAPI backend for the TriPi AI Travel Planner.

Run with:
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import os
import uuid
import traceback
from datetime import datetime
from typing import Optional

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
