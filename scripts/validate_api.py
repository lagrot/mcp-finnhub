import os
import sys
import finnhub
from dotenv import load_dotenv

def validate_api():
    # Load environment variables from .env
    load_dotenv()
    
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        print("❌ Error: FINNHUB_API_KEY not found in environment or .env file.")
        sys.exit(1)
    
    print(f"🔍 Validating API key starting with: {api_key[:4]}...")
    
    client = finnhub.Client(api_key=api_key)
    try:
        # Simple, low-cost call to verify the key (e.g., AAPL profile)
        client.company_profile2(symbol="AAPL")
        print("✅ Success! API key is valid and working.")
    except Exception as e:
        print(f"❌ Error: API validation failed. Details: {e}")
        sys.exit(1)

if __name__ == "__main__":
    validate_api()
