"""LangGraph ReAct agent for TriPi travel planner."""

from __future__ import annotations

import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from agent.prompts import SYSTEM_PROMPT
from tools.weather import weather_lookup
from tools.destination import destination_info
from tools.web_search import web_search
from tools.places import places_search
from tools.currency import currency_convert
from tools.knowledge import knowledge_search


def _get_optional_tools() -> list:
    """Import premium tools if their dependencies are available."""
    optional = []
    try:
        from tools.flights import flight_search
        optional.append(flight_search)
    except ImportError:
        pass
    try:
        from tools.hotels import hotel_search
        optional.append(hotel_search)
    except ImportError:
        pass
    return optional


def build_agent(api_key: str | None = None):
    """Build and return the LangGraph ReAct travel planning agent.

    Args:
        api_key: Google API key. Falls back to GOOGLE_API_KEY env var.

    Returns:
        A compiled LangGraph agent that can be invoked with messages.
    """
    key = api_key or os.getenv("GOOGLE_API_KEY", "")

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        google_api_key=key,
        temperature=0.7,
        max_output_tokens=8192,
    )

    tools = [
        weather_lookup,
        destination_info,
        web_search,
        places_search,
        currency_convert,
        knowledge_search,
        *_get_optional_tools(),
    ]

    memory = MemorySaver()

    # LangGraph v1.2+ uses `state_modifier` for system prompt injection
    agent = create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=memory,
        prompt=SYSTEM_PROMPT,
    )

    return agent
