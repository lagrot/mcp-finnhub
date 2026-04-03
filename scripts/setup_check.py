import os
import sys
import finnhub
from dotenv import load_dotenv

def run_diagnostic():
    """Verify the environment and Finnhub API connection."""
    print("🔍 Starting mcp-finnhub diagnostic check...")
    
    # 1. Environment Loading
    api_key = os.environ.get("FINNHUB_API_KEY")
    origin = "system environment"

    if not api_key:
        load_dotenv()
        api_key = os.environ.get("FINNHUB_API_KEY")
        origin = ".env file"

    if not api_key:
        print("❌ Error: FINNHUB_API_KEY not found. Please set it in your environment or .env file.")
        sys.exit(1)

    # 2. Key Validation (Check for placeholders)
    placeholders = ["YOUR_API_KEY", "your_api_key", "placeholder"]
    if any(p in api_key.lower() for p in placeholders):
        print(f"❌ Error: Invalid API key found in {origin}: '{api_key}'.")
        sys.exit(1)

    # 3. API Connection Check
    print(f"📡 Testing connection to Finnhub using {origin}...")
    try:
        client = finnhub.Client(api_key=api_key.strip("'\" "))
        profile = client.company_profile2(symbol="AAPL")
        print(f"✅ Success! Connected to Finnhub.")
        print(f"📊 Verified API access (AAPL: {profile.get('name', 'Unknown')})")
    except Exception as e:
        print(f"❌ Error: Finnhub API connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_diagnostic()
