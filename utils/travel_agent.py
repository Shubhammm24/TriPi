import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import google.generativeai as genai
from pydantic import BaseModel
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.chains import ConversationChain

class TravelPreferences(BaseModel):
    budget: str
    duration: int
    start_date: datetime
    end_date: datetime
    start_location: str
    destination: str
    purpose: str
    dietary_preferences: Optional[List[str]] = []
    interests: Optional[List[str]] = []
    mobility_requirements: Optional[str] = None
    accommodation_type: Optional[str] = None
    walking_tolerance: Optional[str] = None
    specific_interests: Optional[Dict[str, List[str]]] = None
    meal_preferences: Optional[Dict[str, str]] = None
    hidden_gems_preference: Optional[bool] = False

class TravelAgent:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)

        generation_config = {
            "temperature": 0.9,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        # Initialize Gemini model for direct generation
        self.model = genai.GenerativeModel(
            "gemini-3.5-flash",
            generation_config=generation_config
        )

        # Initialize LangChain conversation chain for iterative refinement
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash",
            google_api_key=api_key,
            temperature=0.7,
        )
        self.memory = ConversationBufferMemory()
        self.conversation = ConversationChain(
            llm=llm,
            memory=self.memory,
            verbose=False,
        )

        
    def _response_to_text(self, response) -> str:
        """Extract plain text from Gemini responses that may contain multiple parts.

        Handles candidates/content.parts structures and falls back gracefully.
        """
        try:
            # Fast path if SDK still provides .text for simple responses
            if hasattr(response, "text") and isinstance(response.text, str) and response.text:
                return response.text

            parts_text: List[str] = []

            # Preferred: candidates[0].content.parts
            candidates = getattr(response, "candidates", None) or []
            if candidates:
                content = getattr(candidates[0], "content", None)
                parts = getattr(content, "parts", None) or []
                for part in parts:
                    text_val = getattr(part, "text", None)
                    if isinstance(text_val, str):
                        parts_text.append(text_val)
                    elif isinstance(part, dict) and isinstance(part.get("text"), str):
                        parts_text.append(part["text"])

            # Fallback: response.parts
            if not parts_text and hasattr(response, "parts"):
                for part in getattr(response, "parts", []) or []:
                    text_val = getattr(part, "text", None)
                    if isinstance(text_val, str):
                        parts_text.append(text_val)

            return "".join(parts_text).strip()
        except Exception:
            return ""

    def _strip_code_fences(self, text: str) -> str:
        """Remove common markdown code fences like ```json ... ``` or ``` ... ```"""
        t = text.strip()
        if t.startswith("```"):
            # remove first fence line
            lines = t.splitlines()
            # drop first line (``` or ```json)
            lines = lines[1:]
            # remove trailing ``` if present
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            t = "\n".join(lines).strip()
        return t

    def _generate_plain_text(self, prompt: str) -> str:
        """Generate content and extract plain text with a simple retry."""
        last_text = ""
        for _ in range(2):
            response = self.model.generate_content(prompt)
            text = self._response_to_text(response)
            if text:
                return text.strip()
            last_text = text or ""
        return last_text

    def _create_initial_prompt(self) -> str:
        return """You are an expert travel agent AI assistant. Your goal is to help users plan 
        their perfect trip by gathering necessary information and creating personalized itineraries.
        
        Please gather the following essential information from the user:
        1. Budget (specific amount or range)
        2. Trip duration and dates
        3. Starting location and destination
        4. Purpose of travel
        
        Then, dive deeper into preferences:
        1. Dietary Requirements:
           - Any specific dietary restrictions (vegetarian, vegan, gluten-free, etc.)
           - Preferred cuisines
           - Any food allergies
        
        2. Activity Preferences:
           - Interest in local culture and history
           - Adventure activities
           - Shopping preferences
           - Art and museum interests
           - Nature and outdoor activities
           - Nightlife preferences
        
        3. Mobility and Accessibility:
           - Walking tolerance (hours per day)
           - Need for accessibility accommodations
           - Preferred transportation methods
        
        4. Accommodation Details:
           - Preferred type (hotel, hostel, apartment)
           - Must-have amenities
           - Location preferences (city center, quiet area)
        
        5. Special Interests:
           - Hidden gems vs. popular attractions
           - Local experiences
           - Photography spots
           - Special events or festivals
        
        Be conversational and friendly while gathering this information."""

    def _get_destination_info(self, destination: str) -> Dict:
        """Use AI to generate destination information when web search is not available."""
        destination_prompt = f"""Generate detailed travel information for {destination} including:
        1. Top 5 must-visit attractions
        2. 3 hidden gems or local secrets
        3. 5 recommended restaurants (mix of cuisines and price ranges)
        4. Current popular events or seasonal activities
        
        Format the response as a JSON with these keys: attractions, hidden_gems, restaurants, events.
        Each should be a list of strings with brief descriptions."""

        try:
            info_text = self._generate_plain_text(destination_prompt)
            info_text = self._strip_code_fences(info_text)
            # Be resilient: try to locate JSON braces if there is extra text
            try:
                destination_data = json.loads(info_text)
            except Exception:
                start = info_text.find('{')
                end = info_text.rfind('}')
                if start != -1 and end != -1 and end > start:
                    destination_data = json.loads(info_text[start:end+1])
                else:
                    raise
            return destination_data
        except Exception:
          
            return {
                "attractions": [
                    "Popular Landmark 1",
                    "Historic Site 1",
                    "Cultural Center",
                    "Local Market",
                    "City Park"
                ],
                "hidden_gems": [
                    "Local Secret Spot 1",
                    "Off-beaten Path Location",
                    "Local Favorite Place"
                ],
                "restaurants": [
                    "Local Cuisine Restaurant",
                    "Fine Dining Option",
                    "Casual Eatery",
                    "Street Food Spot",
                    "Cultural Restaurant"
                ],
                "events": [
                    "Local Festival",
                    "Cultural Event",
                    "Seasonal Activity"
                ]
            }

    def generate_itinerary(self, preferences: TravelPreferences, feedback: str = "") -> str:
        """Generate a complete, personalized travel itinerary."""
        try:
           
            destination_info = self._get_destination_info(preferences.destination)

            
            def stringify_list(items):
                result = []
                for item in items:
                    if isinstance(item, dict):
                        
                        result.append("; ".join(f"{k}: {v}" for k, v in item.items()))
                    else:
                        result.append(str(item))
                return result

            attractions = stringify_list(destination_info.get("attractions", []))
            hidden_gems = stringify_list(destination_info.get("hidden_gems", []))
            restaurants = stringify_list(destination_info.get("restaurants", []))
            events = stringify_list(destination_info.get("events", []))

            
            itinerary_prompt = f"""Create a detailed {preferences.duration}-day travel itinerary for a trip to {preferences.destination}.
    Trip Details:
    - Budget: {preferences.budget}
    - Dates: {preferences.start_date.strftime('%Y-%m-%d')} to {preferences.end_date.strftime('%Y-%m-%d')}
    - Purpose: {preferences.purpose}
    - Interests: {', '.join(preferences.interests) if preferences.interests else 'Various activities'}
    - Dietary Preferences: {', '.join(preferences.dietary_preferences) if preferences.dietary_preferences else 'No restrictions'}
    - Mobility: {preferences.mobility_requirements} (Can walk for {preferences.walking_tolerance})
    - Accommodation: {preferences.accommodation_type}

    Available Attractions: {', '.join(attractions)}
    Hidden Gems: {', '.join(hidden_gems)}
    Restaurants: {', '.join(restaurants)}
    Events: {', '.join(events)}

    Please create a day-by-day itinerary that:
    1. Starts each day with a breakfast recommendation
    2. Groups nearby attractions together to minimize travel time
    3. Includes specific timing for each activity
    4. Suggests restaurants that match dietary preferences
    5. Incorporates rest periods and flexible time
    6. Provides transportation recommendations
    7. Includes estimated costs for activities
    8. Suggests indoor alternatives for bad weather
    9. Balances tourist attractions with hidden gems
    10. Considers walking tolerance and mobility needs

    Format the itinerary clearly with day numbers, times, and sections for morning, afternoon, and evening."""

            
            itinerary_text = self._generate_plain_text(itinerary_prompt)
            if not itinerary_text:
                return "Unable to generate itinerary. Please try again."

            
            full_itinerary = f"""Personalized Travel Itinerary for {preferences.destination}
    Duration: {preferences.duration} days
    Dates: {preferences.start_date.strftime('%Y-%m-%d')} to {preferences.end_date.strftime('%Y-%m-%d')}
    Budget: {preferences.budget}
    {itinerary_text}

    Practical Information:
    - Emergency Numbers: Save local emergency contacts
    - Weather: Check daily forecast
    - Transportation: Download local transit apps
    - Bookings: Make reservations in advance
    - Local Customs: Research and respect local traditions"""

            return full_itinerary.strip()

        except Exception as e:
            return f"An error occurred while generating the itinerary: {str(e)}"
    
    def refine_suggestions(self, preferences: TravelPreferences, feedback: str) -> str:
        """Now uses LangChain to remember all past feedback"""
        try:
            context = f"""
            Original trip: {preferences.destination} for {preferences.duration} days
            Budget: {preferences.budget}, Purpose: {preferences.purpose}
            Interests: {', '.join(preferences.interests or [])}
            Dietary: {', '.join(preferences.dietary_preferences or [])}
            Mobility: {preferences.walking_tolerance}
            User feedback: {feedback}
            """
            
            response = self.conversation.predict(input=context)
            return response
        except Exception as e:
            return f"Sorry, I couldn't refine the itinerary right now: {str(e)}"


