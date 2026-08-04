"""Agent state schema for TriPi travel planner."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Optional

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class TripRequest(BaseModel):
    """Structured user input gathered from the preference form."""

    budget: str = Field(description="Budget range or amount, e.g. '$2000' or '$1000-3000'")
    duration: int = Field(description="Trip duration in days")
    start_date: datetime = Field(description="Trip start date")
    end_date: datetime = Field(description="Trip end date")
    origin: str = Field(description="Starting city/location")
    destination: str = Field(description="Target destination")
    purpose: str = Field(default="Leisure", description="Purpose of travel")
    interests: list[str] = Field(default_factory=list, description="Activity interests")
    dietary_preferences: list[str] = Field(default_factory=list, description="Dietary restrictions")
    mobility_requirements: Optional[str] = Field(default=None, description="Mobility needs")
    accommodation_type: Optional[str] = Field(default=None, description="Accommodation preference")
    walking_tolerance: Optional[str] = Field(default=None, description="Walking comfort level")
    hidden_gems_preference: bool = Field(default=False, description="Prefer hidden gems")
    cuisine_preferences: list[str] = Field(default_factory=list, description="Preferred cuisines")
    amenities: list[str] = Field(default_factory=list, description="Must-have amenities")


class AgentState(dict):
    """LangGraph state passed between nodes in the ReAct agent.

    Uses ``Annotated[list, add_messages]`` so LangGraph merges messages
    correctly across graph steps.
    """

    messages: Annotated[list[AnyMessage], add_messages]
    trip_request: Optional[TripRequest]
    weather_data: Optional[dict]
    destination_data: Optional[dict]
    places_data: Optional[list[dict]]
    flight_options: Optional[list[dict]]
    hotel_options: Optional[list[dict]]
    itinerary: Optional[str]
