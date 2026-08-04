"""Tools __init__.py — re-exports all agent tools."""

from tools.weather import weather_lookup  # noqa: F401
from tools.destination import destination_info  # noqa: F401
from tools.web_search import web_search  # noqa: F401
from tools.places import places_search  # noqa: F401
from tools.currency import currency_convert  # noqa: F401
from tools.knowledge import knowledge_search  # noqa: F401

# Optional premium tools (imported separately to avoid hard dependency)
try:
    from tools.flights import flight_search  # noqa: F401
    from tools.hotels import hotel_search  # noqa: F401
except ImportError:
    pass

__all__ = [
    "weather_lookup",
    "destination_info",
    "web_search",
    "places_search",
    "currency_convert",
    "knowledge_search",
    "flight_search",
    "hotel_search",
]
