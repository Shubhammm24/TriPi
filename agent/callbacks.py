"""Streaming callbacks for the TriPi agent — used to surface tool activity in the UI."""

from __future__ import annotations

from typing import Any, Callable

from langchain_core.callbacks import BaseCallbackHandler


class ToolActivityCallback(BaseCallbackHandler):
    """Callback handler that fires a user-supplied function whenever a tool starts or finishes.

    This lets the frontend show real-time tool activity indicators like
    "🌤️ Checking weather…" or "✅ Weather data received".
    """

    def __init__(self, on_tool_start: Callable | None = None, on_tool_end: Callable | None = None):
        self.on_tool_start = on_tool_start
        self.on_tool_end = on_tool_end

    def on_tool_start(self, serialized: dict[str, Any], input_str: str, **kwargs: Any) -> None:
        tool_name = serialized.get("name", "unknown_tool")
        if self.on_tool_start:
            self.on_tool_start(tool_name, input_str)

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        if self.on_tool_end:
            self.on_tool_end(output)


TOOL_LABELS = {
    "weather_lookup": "🌤️ Checking weather forecast…",
    "destination_info": "🌍 Looking up destination facts…",
    "web_search": "🔍 Searching the web…",
    "places_search": "📍 Finding attractions & restaurants…",
    "currency_convert": "💰 Converting currency…",
    "knowledge_search": "📚 Searching knowledge base…",
    "flight_search": "✈️ Searching flights…",
    "hotel_search": "🏨 Searching hotels…",
}
