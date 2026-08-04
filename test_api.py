"""Quick test script for the TriPi API."""
import httpx
import json

url = "http://localhost:8000/api/generate"
body = {
    "destination": "Goa",
    "origin": "Bhopal",
    "start_date": "2026-08-08",
    "end_date": "2026-08-10",
    "budget": "20000",
    "duration": 2,
    "purpose": "Leisure",
    "interests": ["Food"],
}

print("Sending request to", url)
print("Body:", json.dumps(body, indent=2))
print("-" * 60)

try:
    resp = httpx.post(url, json=body, timeout=120)
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Session: {data.get('session_id', 'N/A')}")
    print(f"Tools: {data.get('tool_calls', [])}")
    print(f"Error: {data.get('error', 'None')}")
    print(f"Itinerary length: {len(data.get('itinerary', ''))}")
    print("-" * 60)
    itinerary = data.get("itinerary", "EMPTY")
    print(itinerary[:1000] if itinerary else "EMPTY RESPONSE")
except Exception as e:
    print(f"Request failed: {e}")