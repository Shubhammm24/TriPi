"""Destination info tool using REST Countries API (free, no key)."""

import httpx
from langchain_core.tools import tool


@tool
def destination_info(country_or_city: str) -> str:
    """Get country facts: currency, language, timezone, population, and more.

    Uses the REST Countries API (completely free, no key required).

    Args:
        country_or_city: Country name or city's country (e.g. "France", "Japan").

    Returns:
        Formatted destination info string.
    """
    try:
        url = f"https://restcountries.com/v3.1/name/{country_or_city}"
        params = {"fields": "name,capital,currencies,languages,timezones,population,region,subregion,flags,car,idd"}

        with httpx.Client(timeout=10) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        if not data:
            return f"No country data found for: {country_or_city}"

        country = data[0]

        # Extract info
        name = country.get("name", {}).get("common", country_or_city)
        official = country.get("name", {}).get("official", "")
        capital = ", ".join(country.get("capital", ["Unknown"]))
        region = country.get("region", "Unknown")
        subregion = country.get("subregion", "")
        population = country.get("population", 0)
        timezones = ", ".join(country.get("timezones", []))

        # Currencies
        currencies = country.get("currencies", {})
        currency_info = []
        for code, details in currencies.items():
            symbol = details.get("symbol", "")
            cname = details.get("name", "")
            currency_info.append(f"{cname} ({code} {symbol})")
        currency_str = ", ".join(currency_info) if currency_info else "Unknown"

        # Languages
        languages = country.get("languages", {})
        lang_str = ", ".join(languages.values()) if languages else "Unknown"

        # Driving side
        car = country.get("car", {})
        driving_side = car.get("side", "unknown")

        # Phone code
        idd = country.get("idd", {})
        phone_root = idd.get("root", "")
        phone_suffixes = idd.get("suffixes", [])
        phone_code = f"{phone_root}{phone_suffixes[0]}" if phone_suffixes else phone_root

        # Format population
        if population >= 1_000_000:
            pop_str = f"{population / 1_000_000:.1f}M"
        elif population >= 1_000:
            pop_str = f"{population / 1_000:.0f}K"
        else:
            pop_str = str(population)

        lines = [
            f"🌍 Destination Info: {name}",
            f"   Official Name: {official}",
            f"   Capital: {capital}",
            f"   Region: {region}{f' / {subregion}' if subregion else ''}",
            f"   Population: {pop_str}",
            f"   Currency: {currency_str}",
            f"   Languages: {lang_str}",
            f"   Timezones: {timezones}",
            f"   Phone Code: {phone_code}",
            f"   Driving Side: {driving_side.capitalize()}",
        ]

        return "\n".join(lines)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"Country not found: {country_or_city}. Try using the full country name."
        return f"REST Countries API error: {e.response.status_code}"
    except Exception as e:
        return f"Could not fetch destination info: {str(e)}"
