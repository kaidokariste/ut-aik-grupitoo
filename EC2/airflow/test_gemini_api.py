import os
import sys

try:
    import google.generativeai as genai
except ImportError:
    print("Error: 'google-generativeai' package is not installed.")
    print("Please install it using: pip install google-generativeai")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: 'python-dotenv' package is not installed.")
    print("Please install it using: pip install python-dotenv")
    sys.exit(1)

def test_gemini_api():
    # Load environment variables from .env file
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        print("Please set it in your .env file or export it directly.")
        print("Example: export GEMINI_API_KEY='your_api_key_here'")
        sys.exit(1)

    try:
        # Configure the API key
        genai.configure(api_key=api_key)
        
        print("Testing Gemini API connection...")
        
        # Test by listing models
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        print("\nAvailable models:")
        for m in models:
            print(m.name)
            
        if models:
            print("Successfully connected to Gemini API!")
            print(f"Found {len(models)} models supporting content generation.")
            print("\nTesting a simple prompt with gemini-3-flash-preview...")
            
            # Use gemini-3-flash-preview for a quick test
            model = genai.GenerativeModel('gemini-3-flash-preview')
            response = model.generate_content("Hello! Please reply with a short confirmation that the API is working.")
            
            print("\nResponse from Gemini:")
            print("-" * 40)
            print(response.text.strip())
            print("-" * 40)
            print("\nAPI test completed successfully.")
        else:
            print("Connected, but no models found that support generateContent.")
            
    except Exception as e:
        print("\nFailed to connect or test Gemini API.")
        print(f"Error details: {e}")

if __name__ == "__main__":
    test_gemini_api()
