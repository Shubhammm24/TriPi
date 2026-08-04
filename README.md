# TriPi — Agentic AI Travel Planner

TriPi has evolved from a basic Streamlit script into a **modern, full-stack agentic web application**. Powered by LangGraph, Google Gemini, and real-time APIs, it autonomous fetches live data to craft highly personalized day-by-day travel itineraries.

![TriPi Itinerary Planner](https://img.shields.io/badge/Status-Active-success)

## 🚀 Key Features

*   **Autonomous Agent Architecture:** Built on LangGraph, the AI agent dynamically decides which tools to call based on your travel preferences.
*   **Real-time Data Integrations:**
    *   **Google Flights (via SerpApi):** Live flight schedules, airlines, and pricing.
    *   **Open-Meteo:** Live weather forecasting for your travel dates.
    *   **ExchangeRate-API:** Real-time budget conversion into local currency.
    *   **DuckDuckGo Web Search:** Fallback search for current events, train schedules, and live web data.
    *   **REST Countries & Overpass:** Destination insights, local laws, and top POIs.
*   **Knowledge Base (RAG):** Built-in ChromaDB vector store containing curated travel guides (safety, packing, budget tips).
*   **Interactive Refinement:** Chat directly with the agent to swap out restaurants, change plans, or ask for details using conversational memory.
*   **Premium UI/UX:** A stunning "Hyper-Spectral" design system built with Next.js, Framer Motion, and Glassmorphism (dark/light themes).

---

## 🛠️ Technology Stack

*   **Frontend:** Next.js (React), Framer Motion, Vanilla CSS (Glassmorphism design tokens)
*   **Backend:** FastAPI (Python), Uvicorn
*   **AI & Agents:** LangGraph, LangChain, Google Gemini 3.5 Flash
*   **Vector DB:** ChromaDB

---

## ⚙️ Local Setup

### 1. Prerequisites
*   Node.js (v18+)
*   Python (3.10+)

### 2. Clone & Environment Variables
Clone the repository and create a `.env` file in the root directory:

```env
# Required
GOOGLE_API_KEY=your_google_gemini_api_key

# Optional (for live flight search)
SERPAPI_API_KEY=your_serpapi_key

# Optional (for Amadeus Hotels/Flights if preferred)
AMADEUS_API_KEY=your_amadeus_api_key
AMADEUS_API_SECRET=your_amadeus_api_secret
```

### 3. Backend Setup (FastAPI)
Open a terminal in the root directory:

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # On Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Seed the RAG vector store
python -m rag.ingest

# Run the server
python -m uvicorn main:app --reload --port 8000
```
*The backend API will run at `http://localhost:8000`*

### 4. Frontend Setup (Next.js)
Open a **new** terminal in the `frontend` directory:

```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```
*The UI will run at `http://localhost:3000`*

---

## 🗺️ Project Structure

```text
.
├── agent/              # LangGraph ReAct agent & system prompts
├── frontend/           # Next.js web application
│   ├── src/app/        # Pages (Landing, Plan) & Global CSS
│   └── public/         # Static assets
├── rag/                # ChromaDB vector store & markdown knowledge docs
├── tools/              # Agent tools (flights, weather, search, etc.)
├── main.py             # FastAPI server entry point
├── requirements.txt    # Python dependencies
└── .env                # API keys
```

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
