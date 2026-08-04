"""Currency conversion tool using free exchange rate API."""

import httpx
from langchain_core.tools import tool


@tool
def currency_convert(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount between currencies using live exchange rates.

    Uses the free ExchangeRate-API (no key required for open endpoint).

    Args:
        amount: The amount to convert.
        from_currency: Source currency code (e.g. "USD", "EUR", "INR").
        to_currency: Target currency code (e.g. "JPY", "GBP", "THB").

    Returns:
        Formatted conversion result string.
    """
    from_currency = from_currency.upper().strip()
    to_currency = to_currency.upper().strip()

    try:
        url = f"https://open.er-api.com/v6/latest/{from_currency}"

        with httpx.Client(timeout=10) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()

        if data.get("result") != "success":
            return f"Currency API error: {data.get('error-type', 'unknown error')}"

        rates = data.get("rates", {})

        if to_currency not in rates:
            return (
                f"Currency code '{to_currency}' not found. "
                f"Available codes include: {', '.join(list(rates.keys())[:20])}..."
            )

        rate = rates[to_currency]
        converted = amount * rate

        return (
            f"💰 Currency Conversion\n"
            f"   {amount:,.2f} {from_currency} = {converted:,.2f} {to_currency}\n"
            f"   Exchange Rate: 1 {from_currency} = {rate:,.4f} {to_currency}\n"
            f"   Last Updated: {data.get('time_last_update_utc', 'Unknown')}"
        )

    except httpx.HTTPStatusError as e:
        return f"Currency API error: HTTP {e.response.status_code}"
    except Exception as e:
        return f"Could not convert currency: {str(e)}"
