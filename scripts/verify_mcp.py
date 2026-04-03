import os
from mcp_finnhub.server import mcp
from dotenv import load_dotenv

def verify_mcp():
    # Load .env (if present) to mirror the server's startup behavior
    load_dotenv()
    
    print("🚀 Verifying MCP tool: get_company_profile...")
    try:
        # Call the tool directly through the FastMCP instance
        # Note: In FastMCP, tools are accessible via the instance
        # We need to find the tool function. FastMCP stores tools in its internal registry.
        
        # Simpler: just call the function directly as it's exported in server.py
        from mcp_finnhub.server import get_company_profile
        
        result = get_company_profile(symbol="AAPL")
        
        if "error" in result:
            print(f"❌ MCP Tool Error: {result['error']}")
        else:
            print(f"✅ Success! Tool returned data for: {result.get('name', 'Unknown')}")
            # print(result) # Optional: print full result for debugging
            
    except Exception as e:
        print(f"❌ Unexpected error during MCP verification: {e}")

if __name__ == "__main__":
    verify_mcp()
