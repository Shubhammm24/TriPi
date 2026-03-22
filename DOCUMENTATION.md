# AI Travel Planner Documentation

## 1. Prompts Used

### System Prompt (Travel Agent Initialization)

```python
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
```

### Destination Information Prompt

```python
destination_prompt = f"""Generate detailed travel information for {destination} including:
1. Top 5 must-visit attractions
2. 3 hidden gems or local secrets
3. 5 recommended restaurants (mix of cuisines and price ranges)
4. Current popular events or seasonal activities

Format the response as a JSON with these keys: attractions, hidden_gems, restaurants, events.
Each should be a list of strings with brief descriptions."""
```

### Daily Schedule Generation Prompt

```python
morning_prompt = f"""Create a detailed morning schedule for day {day_num} in {destination},
considering the following preferences:
- Walking tolerance: {preferences.walking_tolerance}
- Dietary preferences: {', '.join(preferences.dietary_preferences)}
- Available attractions: {', '.join(attractions[:3])}
- Breakfast options: {', '.join(restaurants[:2])}"""

afternoon_prompt = """Create an afternoon schedule that includes:
- Lunch recommendations
- Main attractions or activities
- Rest periods
- Alternative indoor options in case of bad weather"""

evening_prompt = """Plan an evening that includes:
- Dinner recommendations
- Evening activities or entertainment
- Transportation back to accommodation"""
```

## 2. Sample Inputs and Outputs

### Sample Input 1

```json
{
  "budget": "$2000-3000",
  "duration": 3,
  "start_date": "2024-04-01",
  "end_date": "2024-04-04",
  "start_location": "New York",
  "destination": "Paris",
  "purpose": "Cultural",
  "dietary_preferences": ["Vegetarian"],
  "interests": ["History & Culture", "Art & Museums", "Food & Dining"],
  "mobility_requirements": "No special requirements",
  "walking_tolerance": "6 hours",
  "accommodation_type": "Mid-range",
  "hidden_gems_preference": true
}
```

### Sample Output 1

```markdown
# Your Personalized Paris Itinerary

## Trip Overview

Budget: $2000-3000
Duration: 3 days
Dates: April 1-4, 2024
Purpose: Cultural Experience

Day 1:
Morning:

- 8:30 AM: Breakfast at Le Petit Pain, a charming local bakery known for fresh croissants and vegetarian options
- 9:30 AM: Visit the Louvre Museum (skip-the-line tickets recommended)
- Highlights: Mona Lisa, Venus de Milo, Winged Victory

Afternoon:

- 1:00 PM: Lunch at L'As du Fallafel in Le Marais (excellent vegetarian options)
- 2:30 PM: Explore Le Marais district
- Hidden Gem: Visit Musée Carnavalet for Paris history (free entry)
- 4:30 PM: Place des Vosges and Victor Hugo's House

Evening:

- 7:00 PM: Dinner at Le Potager du Marais (vegetarian restaurant)
- 8:30 PM: Seine River evening walk
- 9:30 PM: Eiffel Tower light show viewing from Trocadéro

[Days 2 and 3 continue with similar detailed breakdowns...]
```

### Sample Input 2

```json
{
  "budget": "200000",
  "duration": 5,
  "start_date": "2025-03-28",
  "end_date": "2025-04-02",
  "start_location": "India",
  "destination": "Dubai",
  "purpose": "Leisure",
  "dietary_preferences": ["Vegetarian"],
  "interests": ["History & Culture", "Art & Museums", "Food & Dining", "Local Experiences"],
  "mobility_requirements": "No special requirements",
  "walking_tolerance": "4 hours",
  "accommodation_type": "Mid-range",
  "hidden_gems_preference": false
}
```

### Sample Output 2
```markdown
Personalized Travel Itinerary for Dubai
Duration: 5 days
Dates: 2025-03-28 to 2025-04-02
Budget: 200000
#
5-Day Dubai Itinerary (March 28th - April 2nd, 2025) - Vegetarian Focus
Budget: AED 200,000 (Approx. USD 54,450 - This budget is extremely generous for 5 days and allows for significant flexibility and upgrades if desired.  The itinerary below assumes a more moderate spend within this limit)

Dietary Preferences: Vegetarian

Day 1: Arrival & Downtown Delights
Morning (9:00 AM): Arrive at Dubai International Airport (DXB). Take a pre-booked taxi or the Dubai Metro (Red Line) to your mid-range hotel near Downtown Dubai. (Cost: Taxi - AED 100, Metro - AED 10)
Breakfast (10:00 AM):  Start your day at Comptoir 102 (healthy, organic, vegetarian options). (Cost: AED 80)
Afternoon (11:30 AM): Check in to your hotel and freshen up.
Afternoon (1:00 PM): Explore Dubai Mall. Visit the Dubai Aquarium & Underwater Zoo. (Cost: AED 100).
Late Afternoon (3:00 PM): Relax at a cafe in the mall and enjoy a coffee break.  (Cost: AED 50)
Evening (5:00 PM): Experience the mesmerizing Dubai Fountain show. (Free)
Dinner (6:30 PM): Enjoy a delicious vegetarian Thai meal at Thiptara with views of the Burj Khalifa and fountain. (Cost: AED 200).
Evening (8:30 PM): Ascend the Burj Khalifa for breathtaking nighttime views from the observation deck. (Pre-book tickets online for better prices - Cost: AED 150).
Night (10:00 PM): Return to your hotel.

Day 2: Old Dubai & Cultural Immersion
Morning (8:00 AM): Breakfast at your hotel or at a local cafe serving Arabic breakfast. (Cost: AED 60)
Morning (9:30 AM): Take a taxi or metro to Al Fahidi Historical Neighbourhood (Bastakiya). Explore the narrow alleyways, wind towers, and art galleries. (Cost: Taxi/Metro - AED 30)
Late Morning (11:00 AM): Visit the Dubai Museum to learn about the city's history. (Cost: AED 3)
Midday (12:30 PM): Cross Dubai Creek on an Abra (traditional boat). (Cost: AED 1).
Lunch (1:00 PM): Explore the Spice Souk and Gold Souk, then enjoy a vegetarian lunch at a local restaurant. (Cost: AED 70).
Afternoon (3:00 PM): Visit the Coffee Museum. (Cost: AED 30)
Late Afternoon (4:30 PM): Relax with a traditional Arabic coffee or tea. (Cost: AED 20)
Evening (6:00 PM): Dinner at Ravi Restaurant for authentic and affordable Pakistani/Indian vegetarian cuisine. (Cost: AED 60)
Night (8:00 PM): Return to the hotel.


Day 3: Beach Day & Artistic Exploration
Morning (8:00 AM):  Breakfast at your hotel.
Morning (9:00 AM): Take a taxi to Jumeirah Public Beach. Enjoy swimming, sunbathing, or simply relaxing by the sea. (Cost: Taxi - AED 50, Beach Access - Free)
Lunch (1:00 PM): Enjoy a casual vegetarian lunch at a beachside cafe. (Cost: AED 80)
Afternoon (2:30 PM): Explore the vibrant JBR Walk with its shops, cafes, and street performers.
Late Afternoon (4:00 PM): Take a taxi to Alserkal Avenue. Explore the art galleries, studios, and enjoy a coffee at a trendy cafe. (Cost: Taxi - AED 40, Coffee - AED 40)
Dinner (7:00 PM): Find a vegetarian-friendly option amongst Alserkal Avenue’s diverse culinary offerings. (Cost: AED 100)
Night (9:00 PM): Return to your hotel.


Day 4: Desert Adventure & Palm Jumeirah
Morning (8:00 AM):  Breakfast at your hotel.
Morning (9:00 AM): Embark on a desert safari experience. Enjoy dune bashing, camel riding, sandboarding, and cultural performances including a vegetarian dinner. (Pre-book a tour - Cost: AED 300 - includes transport and dinner).
Night (9:00 PM): Return to your hotel.


Day 5: Departure
Morning (8:00 AM): Enjoy a leisurely breakfast at your hotel.
Morning (9:00 AM): Visit the Palm Jumeirah. Take the monorail to Atlantis, The Palm (Cost: AED 30). Explore The Lost Chambers Aquarium (Cost: AED 100).
Lunch (1:00 PM): Vegetarian lunch at a restaurant on Palm Jumeirah. (Cost: AED 100)
Afternoon (3:00 PM):  Return to your hotel, collect your luggage, and head to the airport. (Cost: Taxi - AED 100/Metro - AED 10 depending on hotel location).
Evening (6:00 PM): Depart from DXB.
Notes:

This itinerary provides estimated costs. Actual expenses may vary.

Pre-booking attractions and tours online can often result in better prices.

Transportation costs are estimates. Consider using ride-sharing services like Uber or Careem for convenient travel.

Dubai Metro is a cost-effective and efficient way to travel between many attractions.

For bad weather alternatives, consider indoor attractions like museums, malls, or the IMG Worlds of Adventure indoor theme park.

This itinerary can be adapted to suit your preferences and pace. Feel free to add or remove activities based on your interests.

 Remember to dress respectfully, especially when visiting religious sites.

Carry a reusable water bottle and stay hydrated, especially during outdoor activities.

Enjoy your trip to Dubai!

Practical Information:

- Emergency Numbers: Save local emergency contacts

- Weather: Check daily forecast

- Transportation: Download local transit apps

- Bookings: Make reservations in advance

- Local Customs: Research and respect local traditions
```

## 3. Process Documentation

### Initial Prompt Development

The system prompt was designed to be comprehensive yet conversational. It focuses on gathering all necessary information while maintaining a friendly tone. The structured approach ensures no important details are missed while planning the trip.

### Destination Information Generation

The destination prompt was crafted to provide a balanced mix of popular attractions and hidden gems. The JSON format ensures structured data that can be easily processed and incorporated into the itinerary. The prompt specifically requests varied price ranges for restaurants to accommodate different budgets.

### Daily Schedule Generation

The daily schedule prompts were split into morning, afternoon, and evening segments to ensure detailed attention to each part of the day. They consider user preferences, weather contingencies, and practical aspects like rest periods and transportation. The prompts are designed to create realistic, well-paced itineraries that don't overwhelm travelers.

## 4. Live Application

The AI Travel Planner is hosted on Streamlit Cloud and can be accessed at:
[https://travel-agent-dhruvsaringit.streamlit.app](https://travelagent1.streamlit.app/)

### Features:

- Interactive form for gathering travel preferences
- Real-time itinerary generation
- Itinerary refinement based on feedback
- Responsive design
- Detailed day-by-day planning
- Consideration for dietary restrictions and accessibility needs

### Technical Stack:

- Frontend: Streamlit
- AI Model: Google Gemini Pro
- Deployment: Streamlit Cloud
- Version Control: GitHub
