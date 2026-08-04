"""Flight search tool using SerpApi (Google Flights).

Gracefully degrades if API key is not set.
"""

import os
import httpx
from langchain_core.tools import tool


@tool
def flight_search(origin: str, destination: str, date: str) -> str:
    """Search for flights between two cities on a given date using Google Flights.

    Requires SERPAPI_API_KEY in .env.
    Returns a graceful fallback message if key is not configured.

    Args:
        origin: Origin airport/city code (e.g. "DEL", "JFK", "BHO").
        destination: Destination airport/city code (e.g. "BOM", "CDG", "GOI").
        date: Departure date in YYYY-MM-DD format.

    Returns:
        Formatted flight options or fallback message.
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    
    if not api_key:
        return (
            "✈️ Flight search is unavailable — SerpApi key not configured.\n"
            "   The AI agent will estimate flight costs based on its knowledge."
        )

    try:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_flights",
            "departure_id": origin.upper(),
            "arrival_id": destination.upper(),
            "outbound_date": date,
            "currency": "USD",
            "hl": "en",
            "type": "2",  # 2 = One way
            "api_key": api_key,
        }

        with httpx.Client(timeout=20) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        flights = data.get("best_flights", [])
        if not flights:
            flights = data.get("other_flights", [])
            
        if not flights:
            return f"No flights found from {origin} to {destination} on {date}."

        lines = [f"✈️ Google Flights: {origin} → {destination} on {date}\n"]

        for i, offer in enumerate(flights[:5], 1):
            price = offer.get("price", "?")
            duration = offer.get("total_duration", 0) / 60  # total duration in minutes
            duration_hrs = int(duration // 60)
            duration_mins = int(duration % 60)
            duration_str = f"{duration_hrs}h {duration_mins}m"
            
            legs = offer.get("flights", [])
            stops = len(legs) - 1 if legs else 0
            stop_str = "Direct" if stops == 0 else f"{stops} stop{'s' if stops > 1 else ''}"
            
            if legs:
                dep_time = legs[0].get("departure_airport", {}).get("time", "?")[-5:]
                arr_time = legs[-1].get("arrival_airport", {}).get("time", "?")[-5:]
                airline = legs[0].get("airline", "Unknown Airline")
                
                lines.append(f"  {i}. {airline} | {dep_time} → {arr_time} | {duration_str} ({stop_str})")
            else:
                lines.append(f"  {i}. Flight details unavailable")

            lines.append(f"     Price: ${price}")
            lines.append("")

        return "\n".join(lines)

    except Exception as e:
        return f"Flight search error: {str(e)}"
