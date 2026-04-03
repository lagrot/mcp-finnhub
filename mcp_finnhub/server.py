import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import finnhub
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env file first.
# This should be in the project root.
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-finnhub")

# Initialize FastMCP
mcp = FastMCP("mcp-finnhub")

# Initialize Finnhub Client lazily
_finnhub_client: finnhub.Client | None = None


def get_finnhub_client() -> finnhub.Client:
    """Get the Finnhub client, prioritizing environment and .env files.
    
    This function is designed to be highly robust and transparent about its 
    key loading process to help troubleshoot environment issues.
    """
    global _finnhub_client
    if _finnhub_client is not None:
        return _finnhub_client

    # Log to a temporary file for external diagnostics
    log_file = "/tmp/mcp-finnhub.log"
    with open(log_file, "a") as f:
        f.write(f"\n--- {datetime.now()} ---\n")
        f.write(f"CWD: {os.getcwd()}\n")

        # Step 1: Priority check: Is it in the environment?
        api_key = os.environ.get("FINNHUB_API_KEY")
        if api_key:
            f.write(f"Key found in environment (starts with {api_key[:4]})\n")
        else:
            f.write("Key NOT found in environment. Attempting .env...\n")
            
        # Step 2: Fallback: Load from .env file
        # This will search starting from the current directory
        load_dotenv()
        api_key = os.environ.get("FINNHUB_API_KEY")
        if api_key:
             f.write(f"Key found after load_dotenv() (starts with {api_key[:4]})\n")
        else:
             f.write("Key STILL NOT found after load_dotenv().\n")

        # Step 3: Validate and Clean the key
        if not api_key or "your_api_key" in api_key.lower():
            f.write(f"ABORTING: Key is invalid or placeholder: '{api_key}'\n")
            error_msg = f"FINNHUB_API_KEY is missing or invalid (found '{api_key}'). Check {log_file} for details."
            logger.error(error_msg)
            raise ValueError(error_msg)

        api_key = api_key.strip("'\" ")
        
        # Step 4: Proactive Validation
        try:
            client = finnhub.Client(api_key=api_key)
            client.company_profile2(symbol="AAPL")
            _finnhub_client = client
            f.write("SUCCESS: Finnhub client initialized and verified.\n")
            return _finnhub_client
        except Exception as e:
            f.write(f"FAILURE: API validation failed: {e}\n")
            logger.error(f"Finnhub API Authentication failed: {e}")
            raise ConnectionError(f"Finnhub API Authentication failed: {e}") from e


# Helper function to return MCP-compatible error responses
def _create_error_response(message: str, original_exception: Exception = None) -> dict[str, Any]:
    """Creates a standardized error response dictionary."""
    error_detail = ""
    if original_exception:
        # Check if it's a Finnhub API exception with a status code
        if hasattr(original_exception, 'status_code'):
            if original_exception.status_code == 403:
                error_detail = " (Access Denied: This endpoint may require a paid Finnhub plan)"
            else:
                error_detail = f" (API Error {original_exception.status_code})"
        
    full_message = f"{message}{error_detail}"
    logger.error(f"Error: {full_message} - Original Exception: {original_exception}")
    return {"error": full_message}


@mcp.tool()
def get_company_profile(symbol: str) -> dict[str, Any]:
    """Get basic company information (name, ticker, industry, market cap, etc.).

    Args:
        symbol: The stock ticker symbol (e.g., AAPL, TSLA).

    """
    logger.info("Fetching company profile for %s", symbol)
    try:
        client = get_finnhub_client()
        return client.company_profile2(symbol=symbol)
    except Exception as e:
        return _create_error_response(f"Failed to fetch company profile for {symbol}.", e)


@mcp.tool()
def get_financial_metrics(symbol: str) -> dict[str, Any]:
    """Get key financial ratios and metrics (P/E, margins, growth, etc.).

    Args:
        symbol: The stock ticker symbol (e.g., AAPL).

    """
    logger.info("Fetching basic financials for %s", symbol)
    try:
        client = get_finnhub_client()
        return client.company_basic_financials(symbol, "all")
    except Exception as e:
        return _create_error_response(f"Failed to fetch financial metrics for {symbol}.", e)


@mcp.tool()
def get_quote(symbol: str) -> dict[str, Any]:
    """Get real-time quote data for a symbol (Price, Change, High, Low, Open, Previous Close).
    
    This is generally available on the Finnhub Free Tier.

    Args:
        symbol: The stock ticker symbol (e.g., AAPL).
    """
    logger.info("Fetching quote for %s", symbol)
    try:
        client = get_finnhub_client()
        return client.quote(symbol)
    except Exception as e:
        return _create_error_response(f"Failed to fetch quote for {symbol}.", e)


@mcp.tool()
def get_recommendation_trends(symbol: str) -> list[dict[str, Any]]:
    """Get latest analyst recommendation trends (Buy/Hold/Sell counts).
    
    This is generally available on the Finnhub Free Tier.

    Args:
        symbol: The stock ticker symbol.
    """
    logger.info("Fetching recommendation trends for %s", symbol)
    try:
        client = get_finnhub_client()
        return client.recommendation_trends(symbol)
    except Exception as e:
        return _create_error_response(f"Failed to fetch recommendations for {symbol}.", e)


@mcp.tool()
def get_stock_candles(
    symbol: str,
    resolution: str = "D",
    days_back: int = 30,
) -> dict[str, Any]:
    """Get historical stock price data (OHLCV).
    
    NOTE: This endpoint often requires a paid Finnhub plan for certain resolutions or symbols.

    Args:
        symbol: The stock ticker symbol.
        resolution: Candle resolution. '1', '5', '15', '30', '60', 'D', 'W', 'M'.
        days_back: Number of days of historical data to fetch.

    """
    logger.info("Fetching stock candles for %s (res: %s, days: %d)", symbol, resolution, days_back)
    try:
        # Calculate timestamps lazily to avoid issues if datetime is mocked in tests
        to_ts = int(datetime.now(timezone.utc).timestamp())
        from_ts = int((datetime.now(timezone.utc) - timedelta(days=days_back)).timestamp())

        client = get_finnhub_client()
        return client.stock_candles(symbol, resolution, from_ts, to_ts)
    except Exception as e:
        return _create_error_response(f"Failed to fetch stock candles for {symbol}.", e)


@mcp.tool()
def get_company_news(symbol: str, days_back: int = 7) -> list[dict[str, Any]]:
    """Get recent news articles for a specific company.

    Args:
        symbol: The stock ticker symbol.
        days_back: Number of days of news to fetch.

    """
    logger.info("Fetching company news for %s (days_back: %d)", symbol, days_back)
    try:
        to_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        from_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime(
            "%Y-%m-%d",
        )

        client = get_finnhub_client()
        return client.company_news(symbol, _from=from_date, to=to_date)
    except Exception as e:
        return _create_error_response(f"Failed to fetch company news for {symbol}.", e)


@mcp.tool()
def get_market_news(category: str = "general") -> list[dict[str, Any]]:
    """Get general market news.

    Args:
        category: News category. 'general', 'forex', 'crypto', 'merger'.

    """
    logger.info("Fetching general news for category: %s", category)
    try:
        client = get_finnhub_client()
        # Finnhub API's general_news method uses min_id to fetch news.
        # Setting it to 0 fetches recent news.
        return client.general_news(category, min_id=0)
    except Exception as e:
        return _create_error_response(f"Failed to fetch market news for category {category}.", e)


@mcp.tool()
def get_technical_indicators(symbol: str, resolution: str = "D") -> dict[str, Any]:
    """Get aggregate technical indicators (Buy/Sell/Hold signals).

    Args:
        symbol: The stock ticker symbol.
        resolution: Candle resolution. '1', '5', '15', '30', '60', 'D', 'W', 'M'.

    """
    logger.info("Fetching aggregate indicators for %s (res: %s)", symbol, resolution)
    try:
        client = get_finnhub_client()
        return client.aggregate_indicator(symbol, resolution)
    except Exception as e:
        return _create_error_response(f"Failed to fetch technical indicators for {symbol}.", e)


@mcp.tool()
def get_insider_transactions(symbol: str) -> dict[str, Any]:
    """Get recent insider transactions for a company.

    Args:
        symbol: The stock ticker symbol.

    """
    logger.info("Fetching insider transactions for %s", symbol)
    try:
        client = get_finnhub_client()
        # Corrected method name based on finnhub-python library
        return client.stock_insider_transactions(symbol)
    except Exception as e:
        return _create_error_response(f"Failed to fetch insider transactions for {symbol}.", e)


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
