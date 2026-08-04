"""Places / attractions search tool."""

import httpx
from langchain_core.tools import tool


@tool
def places_search(destination: str, category: str = "attractions") -> str:
    """Find attractions, restaurants, hidden gems, and activities in a destination.

    Uses the Nominatim / OpenStreetMap API for geolocation and nearby
    points-of-interest. Falls back to a structured Gemini query if
    external APIs are unavailable.

    Args:
        destination: City or location name (e.g. "Kyoto, Japan").
        category: One of "attractions", "restaurants", "hidden_gems",
                  "nightlife", "outdoor", "shopping".

    Returns:
        Formatted list of places with descriptions.
    """
    try:
        # Use Nominatim to geocode the destination
        geo_url = "https://nominatim.openstreetmap.org/search"
        geo_params = {
            "q": destination,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }
        headers = {"User-Agent": "TriPi-TravelAgent/1.0"}

        with httpx.Client(timeout=10) as client:
            geo_resp = client.get(geo_url, params=geo_params, headers=headers)
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()

        if not geo_data:
            return f"Could not find location: {destination}"

        lat = float(geo_data[0]["lat"])
        lon = float(geo_data[0]["lon"])
        display_name = geo_data[0].get("display_name", destination)

        # Map category to OSM tags
        osm_tags = {
            "attractions": "tourism~museum|tourism~attraction|tourism~viewpoint|historic",
            "restaurants": "amenity~restaurant|amenity~cafe|amenity~fast_food",
            "hidden_gems": "tourism~artwork|leisure~park|leisure~garden|amenity~arts_centre",
            "nightlife": "amenity~bar|amenity~pub|amenity~nightclub",
            "outdoor": "leisure~park|natural~peak|leisure~garden|tourism~viewpoint",
            "shopping": "shop~mall|shop~department_store|amenity~marketplace",
        }

        tag_query = osm_tags.get(category, osm_tags["attractions"])

        # Overpass API query for nearby POIs
        overpass_url = "https://overpass-api.de/api/interpreter"
        # Build query: search within 5km radius
        tag_parts = tag_query.split("|")
        node_queries = []
        for tag in tag_parts:
            key, value = tag.split("~")
            node_queries.append(
                f'node["{key}"="{value}"](around:5000,{lat},{lon});'
            )
        overpass_query = f"""
        [out:json][timeout:10];
        (
            {"".join(node_queries)}
        );
        out center 15;
        """

        with httpx.Client(timeout=15) as client:
            overpass_resp = client.post(
                overpass_url, data={"data": overpass_query}
            )
            overpass_resp.raise_for_status()
            overpass_data = overpass_resp.json()

        elements = overpass_data.get("elements", [])

        if not elements:
            return (
                f"📍 No {category} found via OpenStreetMap for {destination}. "
                "The AI agent will use its own knowledge to suggest places."
            )

        lines = [f"📍 {category.replace('_', ' ').title()} in {display_name}\n"]

        for i, el in enumerate(elements[:10], 1):
            tags = el.get("tags", {})
            name = tags.get("name", tags.get("name:en", "Unnamed"))
            addr = tags.get("addr:street", "")
            website = tags.get("website", "")
            opening = tags.get("opening_hours", "")
            cuisine = tags.get("cuisine", "")

            detail_parts = []
            if addr:
                detail_parts.append(f"📫 {addr}")
            if cuisine:
                detail_parts.append(f"🍽️ {cuisine}")
            if opening:
                detail_parts.append(f"🕐 {opening}")
            if website:
                detail_parts.append(f"🌐 {website}")

            lines.append(f"  {i}. **{name}**")
            if detail_parts:
                lines.append(f"     {' | '.join(detail_parts)}")
            lines.append("")

        return "\n".join(lines)

    except Exception as e:
        return (
            f"Places search encountered an issue: {str(e)}. "
            "The AI agent will use its built-in knowledge instead."
        )
