"""Hotel search tool using Amadeus API (free test tier).

Gracefully degrades if API keys are not set.
"""

import os

import httpx
from langchain_core.tools import tool


def _get_amadeus_token() -> str | None:
    """Authenticate with Amadeus and return an access token."""
    api_key = os.getenv("AMADEUS_API_KEY")
    api_secret = os.getenv("AMADEUS_API_SECRET")

    if not api_key or not api_secret:
        return None

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                "https://test.api.amadeus.com/v1/security/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": api_key,
                    "client_secret": api_secret,
                },
            )
            resp.raise_for_status()
            return resp.json().get("access_token")
    except Exception:
        return None


@tool
def hotel_search(city: str, checkin: str, checkout: str, adults: int = 1) -> str:
    """Search for hotels in a city for given dates.

    Requires AMADEUS_API_KEY and AMADEUS_API_SECRET in .env.
    Returns a graceful fallback message if keys are not configured.

    Args:
        city: City IATA code (e.g. "PAR" for Paris, "TYO" for Tokyo).
        checkin: Check-in date in YYYY-MM-DD format.
        checkout: Check-out date in YYYY-MM-DD format.
        adults: Number of adults (default 1).

    Returns:
        Formatted hotel options or fallback message.
    """
    token = _get_amadeus_token()
    if not token:
        return (
            "🏨 Hotel search is unavailable — Amadeus API keys not configured.\n"
            "   To enable: add AMADEUS_API_KEY and AMADEUS_API_SECRET to your .env file.\n"
            "   Sign up free at https://developers.amadeus.com\n\n"
            "   💡 The AI agent will recommend accommodations based on its knowledge."
        )

    try:
        # Step 1: Get hotel list by city
        list_url = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
        headers = {"Authorization": f"Bearer {token}"}
        list_params = {"cityCode": city.upper(), "radius": 10, "radiusUnit": "KM"}

        with httpx.Client(timeout=15) as client:
            list_resp = client.get(list_url, params=list_params, headers=headers)
            list_resp.raise_for_status()
            hotels_data = list_resp.json()

        hotels = hotels_data.get("data", [])[:5]
        if not hotels:
            return f"No hotels found in city code: {city}"

        hotel_ids = [h.get("hotelId") for h in hotels if h.get("hotelId")]

        # Step 2: Get offers for these hotels
        offers_url = "https://test.api.amadeus.com/v3/shopping/hotel-offers"
        offers_params = {
            "hotelIds": ",".join(hotel_ids),
            "checkInDate": checkin,
            "checkOutDate": checkout,
            "adults": adults,
            "currency": "USD",
        }

        with httpx.Client(timeout=15) as client:
            offers_resp = client.get(
                offers_url, params=offers_params, headers=headers
            )
            offers_resp.raise_for_status()
            offers_data = offers_resp.json()

        results = offers_data.get("data", [])
        if not results:
            return f"No hotel offers available for {city} on {checkin} to {checkout}."

        lines = [f"🏨 Hotel Options in {city} ({checkin} to {checkout})\n"]

        for i, hotel in enumerate(results[:5], 1):
            h = hotel.get("hotel", {})
            name = h.get("name", "Unknown Hotel")
            rating = h.get("rating", "?")

            offers = hotel.get("offers", [{}])
            if offers:
                price = offers[0].get("price", {})
                total = price.get("total", "?")
                currency = price.get("currency", "USD")
                room = offers[0].get("room", {})
                room_type = room.get("typeEstimated", {}).get("category", "Standard")
            else:
                total = "?"
                currency = "USD"
                room_type = "Standard"

            lines.append(f"  {i}. **{name}** {'⭐' * int(rating) if rating.isdigit() else ''}")
            lines.append(f"     Room: {room_type} | Price: {total} {currency}/night")
            lines.append("")

        return "\n".join(lines)

    except Exception as e:
        return f"Hotel search error: {str(e)}"
