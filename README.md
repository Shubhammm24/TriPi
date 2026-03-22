# AI Travel Planner

An intelligent travel planning assistant that helps users create personalized travel itineraries using AI. The application uses the Google Gemini API and Langchain to provide smart, context-aware travel recommendations and detailed itineraries.

## Features

- Interactive travel preference collection
- Personalized itinerary generation
- Real-time itinerary refinement
- Support for various travel preferences:
  - Budget considerations
  - Dietary restrictions
  - Mobility requirements
  - Activity interests
  - Accommodation preferences

## Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd travel-planner
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up your environment variables:
   - Copy `.env.example` to `.env`
   - Add your Google Gemini API key to the `.env` file:

```
GOOGLE_API_KEY=your_api_key_here
```

## Running the Application

1. Start the Streamlit app:

```bash
streamlit run app.py
```

2. Open your browser and navigate to the URL shown in the terminal (typically http://localhost:8501)

## Usage

1. Fill in your travel preferences:

   - Budget
   - Travel dates
   - Destination
   - Interests and preferences
   - Dietary requirements
   - Mobility needs
   - Accommodation preferences

2. Click "Generate Itinerary" to create your personalized travel plan

3. Review the generated itinerary

4. Provide feedback to refine the itinerary if needed

## Project Structure

```
.
├── README.md
├── requirements.txt
├── .env.example
├── .env
├── app.py
└── utils/
    └── travel_agent.py
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.
