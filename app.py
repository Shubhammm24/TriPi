import streamlit as st
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils.travel_agent import TravelAgent, TravelPreferences

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("Please set up your GOOGLE_API_KEY in the .env file")
    st.stop()

agent = TravelAgent(api_key)

# ---------------------------------------------------------------------------
# Design System (generated via UI/UX Pro Max)
# Style: Aurora UI — vibrant gradients, premium feel
# Colors: Primary #1C1917, Accent #A16207 (gold), Background #FAFAF9
# Typography: DM Sans (Google Fonts)
# Effects: Flowing gradients, smooth 200-300ms transitions, soft shadows
# ---------------------------------------------------------------------------

GLOBAL_CSS = """
<style>
    /* ── Google Font ──────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&display=swap');

    /* ── CSS Custom Properties (Design Tokens) ───────────────── */
    :root {
        --color-primary: #1C1917;
        --color-on-primary: #FFFFFF;
        --color-secondary: #44403C;
        --color-accent: #A16207;
        --color-accent-light: #CA8A04;
        --color-background: #0C0A09;
        --color-surface: #1C1917;
        --color-surface-elevated: #292524;
        --color-foreground: #FAFAF9;
        --color-muted: #A8A29E;
        --color-border: #44403C;
        --color-destructive: #DC2626;
        --font-family: 'DM Sans', system-ui, -apple-system, sans-serif;
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 24px;
        --shadow-sm: 0 1px 3px rgba(0,0,0,0.3);
        --shadow-md: 0 4px 12px rgba(0,0,0,0.4);
        --shadow-lg: 0 8px 32px rgba(0,0,0,0.5);
        --transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* ── Global Reset & Base ─────────────────────────────────── */
    .stApp {
        background: var(--color-background) !important;
        font-family: var(--font-family) !important;
        color: var(--color-foreground) !important;
    }

    /* ── Aurora gradient hero background ──────────────────────── */
    .hero-section {
        background: linear-gradient(135deg, #0C0A09 0%, #1C1917 30%, #292524 60%, #1C1917 100%);
        position: relative;
        overflow: hidden;
        border-radius: var(--radius-xl);
        padding: 3rem 2.5rem;
        margin-bottom: 2rem;
        border: 1px solid var(--color-border);
    }
    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(ellipse at 20% 50%, rgba(161,98,7,0.12) 0%, transparent 50%),
                    radial-gradient(ellipse at 80% 20%, rgba(202,138,4,0.08) 0%, transparent 50%),
                    radial-gradient(ellipse at 50% 80%, rgba(161,98,7,0.06) 0%, transparent 50%);
        animation: aurora 10s ease-in-out infinite alternate;
        pointer-events: none;
    }
    @keyframes aurora {
        0%   { transform: translate(0, 0) rotate(0deg); }
        50%  { transform: translate(-2%, 1%) rotate(1deg); }
        100% { transform: translate(1%, -1%) rotate(-0.5deg); }
    }
    .hero-title {
        font-size: 2.75rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        line-height: 1.1;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #FAFAF9, #CA8A04);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        position: relative;
        z-index: 1;
    }
    .hero-subtitle {
        font-size: 1.15rem;
        color: var(--color-muted);
        font-weight: 400;
        line-height: 1.5;
        position: relative;
        z-index: 1;
    }

    /* ── Section cards ───────────────────────────────────────── */
    .section-card {
        background: var(--color-surface);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-lg);
        padding: 1.75rem;
        margin-bottom: 1.25rem;
        transition: var(--transition);
    }
    .section-card:hover {
        border-color: var(--color-accent);
        box-shadow: 0 0 20px rgba(161,98,7,0.08);
    }
    .section-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: var(--color-foreground);
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .section-title .icon {
        width: 28px;
        height: 28px;
        border-radius: var(--radius-sm);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.9rem;
        background: var(--color-surface-elevated);
        border: 1px solid var(--color-border);
    }

    /* ── Streamlit widget overrides ───────────────────────────── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background: var(--color-surface-elevated) !important;
        border: 1px solid var(--color-border) !important;
        border-radius: var(--radius-md) !important;
        color: var(--color-foreground) !important;
        font-family: var(--font-family) !important;
        transition: var(--transition) !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--color-accent) !important;
        box-shadow: 0 0 0 2px rgba(161,98,7,0.2) !important;
    }

    /* Labels */
    .stTextInput label, .stNumberInput label, .stDateInput label,
    .stSelectbox label, .stMultiSelect label, .stSlider label,
    .stCheckbox label {
        color: var(--color-muted) !important;
        font-family: var(--font-family) !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.02em !important;
    }

    /* Slider */
    .stSlider > div > div > div > div {
        background: var(--color-accent) !important;
    }

    /* ── Primary button ──────────────────────────────────────── */
    .stFormSubmitButton > button,
    button[kind="primary"] {
        background: linear-gradient(135deg, var(--color-accent), var(--color-accent-light)) !important;
        color: var(--color-on-primary) !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        font-family: var(--font-family) !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 0.75rem 2rem !important;
        transition: var(--transition) !important;
        cursor: pointer !important;
        letter-spacing: 0.01em !important;
    }
    .stFormSubmitButton > button:hover,
    button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(161,98,7,0.3) !important;
        filter: brightness(1.1) !important;
    }
    .stFormSubmitButton > button:active {
        transform: translateY(0) !important;
    }

    /* ── Secondary buttons ───────────────────────────────────── */
    .stButton > button {
        background: var(--color-surface-elevated) !important;
        color: var(--color-foreground) !important;
        border: 1px solid var(--color-border) !important;
        border-radius: var(--radius-md) !important;
        font-family: var(--font-family) !important;
        font-weight: 500 !important;
        padding: 0.6rem 1.5rem !important;
        transition: var(--transition) !important;
        cursor: pointer !important;
    }
    .stButton > button:hover {
        border-color: var(--color-accent) !important;
        background: var(--color-surface) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Itinerary display card ───────────────────────────────── */
    .itinerary-card {
        background: linear-gradient(180deg, var(--color-surface) 0%, var(--color-background) 100%);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-xl);
        padding: 2.5rem;
        margin: 1.5rem 0;
        position: relative;
        overflow: hidden;
    }
    .itinerary-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--color-accent), var(--color-accent-light), var(--color-accent));
    }
    .itinerary-card h1 {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--color-foreground);
        margin-bottom: 1.5rem;
        letter-spacing: -0.01em;
    }
    .itinerary-card h2 {
        font-size: 1.35rem;
        font-weight: 600;
        color: var(--color-accent-light);
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--color-border);
    }
    .itinerary-card .day-header {
        font-size: 1.2rem;
        font-weight: 600;
        color: var(--color-foreground);
        background: var(--color-surface-elevated);
        padding: 0.75rem 1.25rem;
        border-radius: var(--radius-md);
        margin: 1.75rem 0 1rem 0;
        border-left: 3px solid var(--color-accent);
    }
    .itinerary-card ul {
        margin: 0.75rem 0 1.25rem 1.5rem;
        padding: 0;
    }
    .itinerary-card li {
        margin-bottom: 0.5rem;
        line-height: 1.7;
        color: var(--color-foreground);
        font-size: 0.95rem;
    }
    .itinerary-card p {
        line-height: 1.7;
        color: var(--color-foreground);
        margin-bottom: 1rem;
        font-size: 0.95rem;
    }
    .itinerary-card .time-badge {
        display: inline-block;
        background: var(--color-surface-elevated);
        color: var(--color-accent-light);
        padding: 0.15rem 0.5rem;
        border-radius: var(--radius-sm);
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.35rem;
        border: 1px solid var(--color-border);
    }
    .itinerary-card .cost-tag {
        color: var(--color-accent-light);
        font-weight: 500;
        font-style: italic;
        opacity: 0.9;
    }
    .itinerary-card .note-block {
        background: var(--color-surface-elevated);
        border-left: 3px solid var(--color-accent);
        padding: 1rem 1.25rem;
        border-radius: 0 var(--radius-md) var(--radius-md) 0;
        margin: 1rem 0;
        font-style: italic;
        color: var(--color-muted);
        font-size: 0.9rem;
    }
    .itinerary-card .transport-block {
        color: var(--color-muted);
        font-size: 0.9rem;
        padding: 0.5rem 0;
    }

    /* ── Trip summary chips ──────────────────────────────────── */
    .trip-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        background: var(--color-surface-elevated);
        border: 1px solid var(--color-border);
        border-radius: 100px;
        padding: 0.35rem 0.85rem;
        font-size: 0.8rem;
        color: var(--color-muted);
        margin: 0.25rem;
        transition: var(--transition);
    }
    .trip-chip .chip-value {
        color: var(--color-foreground);
        font-weight: 600;
    }

    /* ── Refinement section ───────────────────────────────────── */
    .refine-section {
        background: var(--color-surface);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-lg);
        padding: 1.75rem;
        margin-top: 1.5rem;
    }
    .refine-section h3 {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--color-foreground);
        margin-bottom: 1rem;
    }

    /* ── Expandable tips ─────────────────────────────────────── */
    .streamlit-expanderHeader {
        background: var(--color-surface) !important;
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--color-border) !important;
        font-family: var(--font-family) !important;
        color: var(--color-foreground) !important;
    }

    /* ── Spinner override ────────────────────────────────────── */
    .stSpinner > div {
        border-color: var(--color-accent) transparent transparent transparent !important;
    }

    /* ── TextArea override ───────────────────────────────────── */
    .stTextArea textarea {
        background: var(--color-surface-elevated) !important;
        border: 1px solid var(--color-border) !important;
        border-radius: var(--radius-md) !important;
        color: var(--color-foreground) !important;
        font-family: var(--font-family) !important;
        transition: var(--transition) !important;
    }
    .stTextArea textarea:focus {
        border-color: var(--color-accent) !important;
        box-shadow: 0 0 0 2px rgba(161,98,7,0.2) !important;
    }

    /* ── Tab styling ─────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: var(--color-surface) !important;
        border-radius: var(--radius-md);
        padding: 0.35rem;
        border: 1px solid var(--color-border);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-sm) !important;
        font-family: var(--font-family) !important;
        font-weight: 500 !important;
        color: var(--color-muted) !important;
        padding: 0.5rem 1rem !important;
        transition: var(--transition) !important;
    }
    .stTabs [aria-selected="true"] {
        background: var(--color-surface-elevated) !important;
        color: var(--color-accent-light) !important;
        font-weight: 600 !important;
    }

    /* ── Markdown headings in main ────────────────────────────── */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: var(--font-family) !important;
        color: var(--color-foreground) !important;
    }
    .stMarkdown p, .stMarkdown li {
        font-family: var(--font-family) !important;
        color: var(--color-foreground) !important;
    }

    /* ── Hide Streamlit default branding ──────────────────────── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* ── Reduce default padding ──────────────────────────────── */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1100px !important;
    }
</style>
"""


def format_itinerary_html(text: str) -> str:
    """Parse raw Gemini itinerary text into styled HTML cards."""
    import re
    lines = text.split('\n')
    html_parts = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            continue

        # Strip markdown bold
        stripped = stripped.replace('**', '')
        # Strip leading bullet markers
        if stripped.startswith('* ') or stripped.startswith('• '):
            stripped = stripped[2:]
        if stripped.startswith('- '):
            stripped = stripped[2:]

        # ── Day headers ──
        if re.match(r'^Day\s+\d+', stripped, re.IGNORECASE):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<div class="day-header">{stripped}</div>')
            continue

        # ── Section headers (Morning, Afternoon, Evening, etc.) ──
        if re.match(r'^(Morning|Afternoon|Evening|Night|Lunch|Dinner|Breakfast)\s*[:.]', stripped, re.IGNORECASE):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h2>{stripped}</h2>')
            continue

        # ── Markdown headings ──
        if stripped.startswith('### '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h2>{stripped[4:]}</h2>')
            continue
        if stripped.startswith('## '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h2>{stripped[3:]}</h2>')
            continue
        if stripped.startswith('# '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h1>{stripped[2:]}</h1>')
            continue

        # ── Time badges (e.g. "9:00 AM: ..." or "10 AM - ...") ──
        time_match = re.match(r'^(\d{1,2}[:.]\d{2}\s*(?:AM|PM|am|pm))\s*[:\-–]\s*(.*)', stripped)
        if not time_match:
            time_match = re.match(r'^(\d{1,2}\s*(?:AM|PM|am|pm))\s*[:\-–]\s*(.*)', stripped)
        if time_match:
            time_str = time_match.group(1)
            rest = time_match.group(2)
            stripped = f'<span class="time-badge">{time_str}</span> {rest}'

        # ── Cost tags ──
        cost_match = re.search(r'(\([^)]*(?:AED|USD|\$|€|£|₹|Cost)[^)]*\))', stripped, re.IGNORECASE)
        if cost_match:
            cost_part = cost_match.group(1)
            stripped = stripped.replace(cost_part, f'<span class="cost-tag">{cost_part}</span>')

        # ── Note/Tip blocks ──
        if re.match(r'^(Note|Tip|Important|Remember|Pro tip)\s*:', stripped, re.IGNORECASE):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<div class="note-block">{stripped}</div>')
            continue

        # ── Transportation blocks ──
        if stripped.lower().startswith('transportation'):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<div class="transport-block">{stripped}</div>')
            continue

        # ── Default: list items ──
        if not in_list:
            html_parts.append('<ul>')
            in_list = True
        html_parts.append(f'<li>{stripped}</li>')

    if in_list:
        html_parts.append('</ul>')

    return '\n'.join(html_parts)


def render_trip_chips(prefs: TravelPreferences):
    """Render trip summary as stylish chips."""
    chips = [
        ("Budget", prefs.budget),
        ("Duration", f"{prefs.duration} days"),
        ("From", prefs.start_location),
        ("To", prefs.destination),
        ("Purpose", prefs.purpose),
    ]
    if prefs.accommodation_type:
        chips.append(("Stay", prefs.accommodation_type))
    if prefs.walking_tolerance:
        chips.append(("Walking", prefs.walking_tolerance))

    chip_html = ''.join(
        f'<span class="trip-chip">{label}: <span class="chip-value">{value}</span></span>'
        for label, value in chips if value
    )
    return f'<div style="margin: 1rem 0; display: flex; flex-wrap: wrap; gap: 0.35rem;">{chip_html}</div>'


def main():
    st.set_page_config(
        page_title="TriPi — AI Travel Planner",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Inject global CSS
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    # ── Session state init ──
    if 'stage' not in st.session_state:
        st.session_state.stage = 'gather_info'
    if 'preferences' not in st.session_state:
        st.session_state.preferences = None
    if 'itinerary' not in st.session_state:
        st.session_state.itinerary = None

    # ══════════════════════════════════════════════════════════════
    #  STAGE 1 — Gather Preferences
    # ══════════════════════════════════════════════════════════════
    if st.session_state.stage == 'gather_info':

        # Hero section
        st.markdown("""
        <div class="hero-section">
            <div class="hero-title">TriPi</div>
            <div class="hero-subtitle">
                Your AI travel planner. Tell us your dream trip and we'll craft<br>
                a personalized, day-by-day itinerary in seconds.
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("travel_preferences"):

            # ── Essential Info ──
            st.markdown('<div class="section-card"><div class="section-title"><span class="icon">📍</span> Trip Essentials</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                budget = st.text_input("Budget (e.g. $2000 or $1000–3000)")
                start_location = st.text_input("Traveling from")
                purpose = st.selectbox("Purpose of travel",
                    ["Leisure", "Business", "Adventure", "Cultural", "Relaxation"])
            with col2:
                destination = st.text_input("Destination")
                start_date = st.date_input("Start date", min_value=datetime.today())
                duration = st.number_input("Duration (days)", min_value=1, value=3)
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Dietary ──
            st.markdown('<div class="section-card"><div class="section-title"><span class="icon">🍽️</span> Dietary Preferences</div>', unsafe_allow_html=True)
            col3, col4 = st.columns(2)
            with col3:
                dietary_prefs = st.multiselect("Dietary restrictions",
                    ["Vegetarian", "Vegan", "Halal", "Kosher", "Gluten-free", "None"])
            with col4:
                cuisine_prefs = st.multiselect("Preferred cuisines",
                    ["Local", "Italian", "Japanese", "Indian", "Mexican", "Mediterranean", "Thai", "French"])
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Activities ──
            st.markdown('<div class="section-card"><div class="section-title"><span class="icon">🎯</span> Activities & Interests</div>', unsafe_allow_html=True)
            interests = st.multiselect("What interests you?",
                ["History & Culture", "Food & Dining", "Nature & Outdoors",
                 "Shopping", "Art & Museums", "Nightlife", "Local Experiences",
                 "Photography", "Adventure Sports", "Wellness & Spa"])
            hidden_gems = st.checkbox("Prefer hidden gems over tourist hotspots")
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Mobility & Accommodation ──
            st.markdown('<div class="section-card"><div class="section-title"><span class="icon">🏨</span> Mobility & Accommodation</div>', unsafe_allow_html=True)
            col5, col6 = st.columns(2)
            with col5:
                mobility = st.selectbox("Mobility requirements",
                    ["No special requirements", "Minimal walking", "Wheelchair accessible",
                     "Prefer public transport"])
                walking_hours = st.slider("Hours comfortable walking/day", 0, 12, 4)
            with col6:
                accommodation = st.selectbox("Accommodation preference",
                    ["Budget", "Mid-range", "Luxury", "Boutique", "Apartment/Airbnb"])
                amenities = st.multiselect("Must-have amenities",
                    ["Wi-Fi", "Pool", "Gym", "Restaurant", "Room Service", "Parking", "Breakfast"])
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Submit ──
            if st.form_submit_button("✨  Generate My Itinerary"):
                missing = []
                if not budget.strip():
                    missing.append("Budget")
                if not destination.strip():
                    missing.append("Destination")
                if not start_location.strip():
                    missing.append("Traveling from")

                if missing:
                    st.error(f"Please fill in: **{', '.join(missing)}**")
                else:
                    end_date = start_date + timedelta(days=duration)
                    preferences = TravelPreferences(
                        budget=budget.strip(),
                        duration=duration,
                        start_date=datetime.combine(start_date, datetime.min.time()),
                        end_date=datetime.combine(end_date, datetime.min.time()),
                        start_location=start_location.strip(),
                        destination=destination.strip(),
                        purpose=purpose,
                        interests=interests,
                        dietary_preferences=dietary_prefs,
                        mobility_requirements=mobility,
                        accommodation_type=accommodation,
                        walking_tolerance=f"{walking_hours} hours",
                        specific_interests={"cuisines": cuisine_prefs, "amenities": amenities},
                        hidden_gems_preference=hidden_gems,
                    )
                    st.session_state.preferences = preferences
                    st.session_state.stage = 'show_itinerary'
                    st.rerun()

    # ══════════════════════════════════════════════════════════════
    #  STAGE 2 — Show Itinerary
    # ══════════════════════════════════════════════════════════════
    elif st.session_state.stage == 'show_itinerary':
        prefs = st.session_state.preferences

        if st.session_state.itinerary is None:
            with st.spinner("Crafting your personalized itinerary…"):
                itinerary = agent.generate_itinerary(prefs)
                st.session_state.itinerary = itinerary

        # Hero header
        st.markdown(f"""
        <div class="hero-section" style="padding: 2rem 2.5rem;">
            <div class="hero-title" style="font-size: 2rem;">Your Trip to {prefs.destination}</div>
            <div class="hero-subtitle">
                {prefs.start_date.strftime('%b %d')} — {prefs.end_date.strftime('%b %d, %Y')} · {prefs.duration} days · {prefs.purpose}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Trip summary chips
        st.markdown(render_trip_chips(prefs), unsafe_allow_html=True)

        # Itinerary content card
        itinerary_html = format_itinerary_html(st.session_state.itinerary)
        st.markdown(f'<div class="itinerary-card">{itinerary_html}</div>', unsafe_allow_html=True)

        # ── Actions ──
        st.markdown('<div class="refine-section">', unsafe_allow_html=True)
        st.markdown('<h3>Refine Your Itinerary</h3>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("← Start Over"):
                st.session_state.stage = 'gather_info'
                st.session_state.preferences = None
                st.session_state.itinerary = None
                st.rerun()

        with col2:
            feedback = st.text_area(
                "What would you like to change?",
                placeholder="E.g. Add more outdoor activities, swap Day 2 lunch, reduce walking…",
                label_visibility="collapsed",
            )
            if st.button("Refine ✨") and feedback:
                with st.spinner("Refining your itinerary…"):
                    refined = agent.refine_suggestions(prefs, feedback)
                    st.session_state.itinerary = refined
                    st.rerun()

        # ── Travel Tips ──
        with st.expander("🧳 Travel Tips & Resources"):
            st.markdown(f"""
            **Packing reminder** — Check the weather forecast for {prefs.destination} around your travel dates.

            **Smart booking tips:**
            - Book popular attractions and restaurants **2–4 weeks** in advance
            - Download offline maps (Google Maps / Maps.me) before departure
            - Save local emergency numbers and embassy contacts
            - Carry a photocopy of your passport separately from the original
            - Research local customs, tipping etiquette, and dress codes
            - Consider travel insurance for trips over 5 days
            """)


if __name__ == "__main__":
    main()
