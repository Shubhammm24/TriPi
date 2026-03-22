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

def main():
    st.set_page_config(page_title="AI Travel Planner", page_icon="🌎", layout="wide")
    
    st.title("AI Travel Planner 🌎✈️")
    st.write("Let me help you plan your perfect trip!")

    
    if 'stage' not in st.session_state:
        st.session_state.stage = 'gather_info'
    if 'preferences' not in st.session_state:
        st.session_state.preferences = None
    if 'itinerary' not in st.session_state:
        st.session_state.itinerary = None

    
    if st.session_state.stage == 'gather_info':
        with st.form("travel_preferences"):
            st.subheader("Essential Information")
            
            col1, col2 = st.columns(2)
            with col1:
                budget = st.text_input("What's your budget? (e.g., $1000, $2000-3000)")
                start_location = st.text_input("Where are you traveling from?")
                purpose = st.selectbox("Purpose of travel", 
                    ["Leisure", "Business", "Adventure", "Cultural", "Relaxation"])
                
            with col2:
                destination = st.text_input("Where would you like to go?")
                start_date = st.date_input("Start date", min_value=datetime.today())
                duration = st.number_input("How many days?", min_value=1, value=3)

            st.subheader("Dietary Preferences")
            col3, col4 = st.columns(2)
            with col3:
                dietary_prefs = st.multiselect("Dietary restrictions",
                    ["Vegetarian", "Vegan", "Halal", "Kosher", "Gluten-free", "None"])
            with col4:
                cuisine_prefs = st.multiselect("Preferred cuisines",
                    ["Local", "Italian", "Japanese", "Indian", "Mexican", "Mediterranean"])

            st.subheader("Activity Preferences")
            interests = st.multiselect("What are your interests?",
                ["History & Culture", "Food & Dining", "Nature & Outdoors", 
                 "Shopping", "Art & Museums", "Nightlife", "Local Experiences"])
            
            hidden_gems = st.checkbox("I prefer hidden gems over tourist attractions")
            
            st.subheader("Mobility & Accommodation")
            col5, col6 = st.columns(2)
            with col5:
                mobility = st.selectbox("Mobility requirements",
                    ["No special requirements", "Minimal walking", "Wheelchair accessible", 
                     "Prefer public transport"])
                walking_hours = st.slider("Hours comfortable walking per day", 0, 12, 4)
            
            with col6:
                accommodation = st.selectbox("Accommodation preference",
                    ["Budget", "Mid-range", "Luxury", "Boutique", "Apartment/Airbnb"])
                amenities = st.multiselect("Must-have amenities",
                    ["Wi-Fi", "Pool", "Gym", "Restaurant", "Room Service"])

            if st.form_submit_button("Generate Itinerary"):
                end_date = start_date + timedelta(days=duration)
                
                preferences = TravelPreferences(
                    budget=budget,
                    duration=duration,
                    start_date=datetime.combine(start_date, datetime.min.time()),
                    end_date=datetime.combine(end_date, datetime.min.time()),
                    start_location=start_location,
                    destination=destination,
                    purpose=purpose,
                    interests=interests,
                    dietary_preferences=dietary_prefs,
                    mobility_requirements=mobility,
                    accommodation_type=accommodation,
                    walking_tolerance=f"{walking_hours} hours",
                    specific_interests={"cuisines": cuisine_prefs, "amenities": amenities},
                    hidden_gems_preference=hidden_gems
                )
                
                st.session_state.preferences = preferences
                st.session_state.stage = 'show_itinerary'
                st.rerun()

    elif st.session_state.stage == 'show_itinerary':
        if st.session_state.itinerary is None:
            with st.spinner("Generating your personalized itinerary..."):
                itinerary = agent.generate_itinerary(st.session_state.preferences)
                st.session_state.itinerary = itinerary

        st.subheader("Your Personalized Travel Itinerary")
        
        
        st.markdown("""
        <style>
        .itinerary {
            background-color: #1E1E1E;
            color: #FFFFFF;
            padding: 30px;
            border-radius: 10px;
            margin: 10px 0;
            white-space: pre-wrap;
            font-family: 'Inter', sans-serif;
            border: 1px solid #333333;
            line-height: 1.6;
            font-weight: normal;
        }
        .itinerary h1 {
            color: #FFFFFF;
            font-size: 26px;
            font-weight: 700;
            margin-bottom: 25px;
            padding-bottom: 10px;
            letter-spacing: 0.5px;
        }
        .itinerary h2 {
            color: #FFFFFF;
            font-size: 22px;
            font-weight: 600;
            margin-top: 30px;
            margin-bottom: 15px;
            padding-bottom: 5px;
            border-bottom: 1px solid #333333;
        }
        .itinerary .day-title {
            font-size: 20px;
            font-weight: 600;
            margin-top: 25px;
            margin-bottom: 15px;
            padding: 8px 0;
            border-bottom: 1px solid #333333;
        }
        .itinerary ul {
            margin: 10px 0 20px 20px;
            list-style-type: '• ';
        }
        .itinerary li {
            margin-bottom: 8px;
            font-weight: normal;
            line-height: 1.6;
        }
        .itinerary p {
            margin-bottom: 15px;
            font-weight: normal;
        }
        .itinerary .time {
            font-weight: 500;
            margin-right: 5px;
        }
        .itinerary .cost {
            opacity: 0.8;
            font-style: italic;
            font-weight: normal;
        }
        .itinerary .note {
            font-style: italic;
            opacity: 0.9;
            margin: 15px 0;
            padding: 10px;
            border-left: 2px solid #333333;
        }
        .itinerary .transport-info {
            margin: 10px 0;
            padding: 8px 0;
            font-size: 0.95em;
            opacity: 0.9;
        }
        </style>
        """, unsafe_allow_html=True)
        
        def format_itinerary(text):
            lines = text.split('\n')
            formatted_lines = []
            in_list = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
            
                line = line.replace('**', '')
                if line.startswith('* ') or line.startswith('• '):
                    line = line[2:]
                
                
                if line.startswith('Day ') and ':' in line:
                    if in_list:
                        formatted_lines.append('</ul>')
                        in_list = False
                    line = f'<div class="day-title">{line}</div>'
                
                
                elif any(t in line.lower() for t in ['am:', 'pm:', 'am-', 'pm-']):
                    time = line.split(':')[0]
                    rest = ':'.join(line.split(':')[1:])
                    line = f'<span class="time">{time}</span>{rest}'
                
                
                if '(AED' in line:
                    cost_part = line[line.find('('):line.find(')')+1]
                    line = line.replace(cost_part, f'<span class="cost">{cost_part}</span>')
                
                
                if line.lower().startswith('transportation:'):
                    line = f'<div class="transport-info">{line}</div>'
                
                
                elif line.startswith('Note:') or line.startswith('Important:'):
                    line = f'<div class="note">{line}</div>'
                
                
                elif not any(line.startswith(prefix) for prefix in ['Day ', 'Transportation:', 'Note:', 'Important:']):
                    if not in_list:
                        formatted_lines.append('<ul>')
                        in_list = True
                    line = f'<li>{line}</li>'
                else:
                    if in_list:
                        formatted_lines.append('</ul>')
                        in_list = False
                
                formatted_lines.append(line)
            
            if in_list:
                formatted_lines.append('</ul>')
            
            return '\n'.join(formatted_lines)

        
        cleaned_itinerary = format_itinerary(st.session_state.itinerary)
        
        
        cleaned_itinerary = cleaned_itinerary.replace('# ', '<h1>')
        cleaned_itinerary = cleaned_itinerary.replace('## ', '<h2>')
        
        st.markdown(f'<div class="itinerary">{cleaned_itinerary}</div>', unsafe_allow_html=True)

        
        st.subheader("Want to refine your itinerary?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Over"):
                st.session_state.stage = 'gather_info'
                st.session_state.preferences = None
                st.session_state.itinerary = None
                st.rerun()

        with col2:
            feedback = st.text_area(
                "Provide your feedback to refine the itinerary:",
                placeholder="Example: I'd like more outdoor activities in the morning..."
            )
            if st.button("Refine Itinerary") and feedback:
                with st.spinner("Refining your itinerary..."):
                    refined_itinerary = agent.refine_suggestions(
                        st.session_state.preferences, feedback)
                    st.session_state.itinerary = refined_itinerary
                    st.rerun()

        # Additional helpful information
        with st.expander("Travel Tips & Resources"):
            st.markdown("""
            ### Useful Resources
            - Check the weather forecast
            - Book attractions in advance
            - Local transportation options
            - Currency exchange rates
            - Emergency contacts
            """)

if __name__ == "__main__":
    main() 
