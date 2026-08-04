"""Weather lookup tool using Open-Meteo API (free, no key required)."""

import json
from datetime import datetime

import httpx
from langchain_core.tools import tool


@tool
def weather_lookup(city: str, start_date: str, end_date: str) -> str:
    """Get weather forecast for a city between two dates.

    Uses the Open-Meteo free API — no API key required.

    Args:
        city: City name (e.g. "Paris", "Tokyo").
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.

    Returns:
        Formatted weather summary string.
    """
    try:
        # Step 1: Geocode city to lat/lon
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {"name": city, "count": 1, "language": "en", "format": "json"}

        with httpx.Client(timeout=10) as client:
            geo_resp = client.get(geo_url, params=geo_params)
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()

        if not geo_data.get("results"):
            return f"Could not find location: {city}. Please check the city name."

        result = geo_data["results"][0]
        lat = result["latitude"]
        lon = result["longitude"]
        location_name = result.get("name", city)
        country = result.get("country", "")

        # Step 2: Fetch weather forecast
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode,windspeed_10m_max",
            "start_date": start_date,
            "end_date": end_date,
            "timezone": "auto",
        }

        with httpx.Client(timeout=10) as client:
            weather_resp = client.get(weather_url, params=weather_params)
            weather_resp.raise_for_status()
            weather_data = weather_resp.json()

        daily = weather_data.get("daily", {})
        dates = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_sum", [])
        codes = daily.get("weathercode", [])

        # Weather code descriptions
        wmo_codes = {
            0: "Clear sky ☀️",
            1: "Mainly clear 🌤️",
            2: "Partly cloudy ⛅",
            3: "Overcast ☁️",
            45: "Foggy 🌫️",
            48: "Rime fog 🌫️",
            51: "Light drizzle 🌦️",
            53: "Moderate drizzle 🌦️",
            55: "Dense drizzle 🌧️",
            61: "Slight rain 🌧️",
            63: "Moderate rain 🌧️",
            65: "Heavy rain ⛈️",
            71: "Slight snow ❄️",
            73: "Moderate snow ❄️",
            75: "Heavy snow ❄️",
            80: "Rain showers 🌦️",
            81: "Moderate rain showers 🌧️",
            82: "Violent rain showers ⛈️",
            95: "Thunderstorm ⛈️",
        }

        # Format output
        lines = [f"🌤️ Weather Forecast for {location_name}, {country}\n"]
        for i, date in enumerate(dates):
            code = codes[i] if i < len(codes) else 0
            condition = wmo_codes.get(code, f"Code {code}")
            hi = max_temps[i] if i < len(max_temps) else "?"
            lo = min_temps[i] if i < len(min_temps) else "?"
            rain = precip[i] if i < len(precip) else 0
            lines.append(
                f"  {date}: {condition} | High: {hi}°C | Low: {lo}°C | Rain: {rain}mm"
            )

        # Summary
        if max_temps:
            avg_hi = sum(t for t in max_temps if t is not None) / len(max_temps)
            avg_lo = sum(t for t in min_temps if t is not None) / len(min_temps)
            total_rain = sum(r for r in precip if r is not None)
            lines.append(f"\n📊 Summary: Avg High {avg_hi:.0f}°C, Avg Low {avg_lo:.0f}°C, Total Rain {total_rain:.0f}mm")

        return "\n".join(lines)

    except httpx.HTTPStatusError as e:
        return f"Weather API error: {e.response.status_code}"
    except Exception as e:
        return f"Could not fetch weather data: {str(e)}"
