import os
from dotenv import load_dotenv
import google.generativeai as genai

def test_gemini_api():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in .env file")
        return
    
    try:
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Initialize the model
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Test generation
        response = model.generate_content("Say hello!")
        
        print("API Test successful!")
        print("Response:", response.text)
        
    except Exception as e:
        print("Error testing API:", str(e))

if __name__ == "__main__":
    test_gemini_api() 