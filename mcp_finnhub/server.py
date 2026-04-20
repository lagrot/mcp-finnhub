import functools
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import finnhub
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-finnhub")

# Initialize FastMCP
mcp = FastMCP("mcp-finnhub")

# Supported resolutions for candles and technical indicators
SUPPORTED_RESOLUTIONS = {"1", "5", "15", "30", "60", "D", "W", "M"}

# Initialize Finnhub Client lazily
_finnhub_client: finnhub.Client | None = None


def ttl_cache(seconds: int = 60):
    """Simple TTL cache decorator to reduce API load and improve performance."""
    def decorator(func):
        cache = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from args and kwargs
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()
            
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < seconds:
                    logger.debug(f"Cache hit for {func.__name__}{args}")
                    return result
            
            result = func(*args, **kwargs)
            
            # Only cache successful responses (not error dictionaries)
            if isinstance(result, dict) and "error" in result:
                return result
                
            cache[key] = (result, now)
            return result
        return wrapper
    return decorator


def get_finnhub_client() -> finnhub.Client:
    """Get the Finnhub client, prioritizing environment and .env files.
    
    This function uses a robust loading pattern to ensure the API key is 
    correctly retrieved and validated.
    """
    global _finnhub_client
    if _finnhub_client is not None:
        return _finnhub_client

    # Step 1: Priority check: Is it in the environment?
    api_key = os.environ.get("FINNHUB_API_KEY")
    origin = "system environment"

    # Step 2: Fallback: Load from .env file
    if not api_key:
        load_dotenv()
        api_key = os.environ.get("FINNHUB_API_KEY")
        origin = ".env file"

    # Step 3: Validate the key
    # We check if the key is a known placeholder string.
    is_placeholder = False
    if api_key:
        clean_key = api_key.strip().lower()
        is_placeholder = any(clean_key == p for p in ["your_api_key_here", "your_api_key", "placeholder"])
    
    if not api_key or is_placeholder:
        error_msg = f"FINNHUB_API_KEY is missing or invalid (found '{api_key}' from {origin})."
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Clean the key of potential whitespace/quotes
    api_key = api_key.strip("'\" ")

    try:
        client = finnhub.Client(api_key=api_key)
        # Verify the key works with a lightweight call
        client.company_profile2(symbol="AAPL")
        _finnhub_client = client
        logger.info(f"Finnhub client successfully initialized using {origin}")
        return _finnhub_client
    except Exception as e:
        logger.error(f"Finnhub API Authentication failed using {origin}: {e}")
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
@ttl_cache(seconds=3600)  # Profile data changes slowly
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
@ttl_cache(seconds=3600)  # Financial metrics change slowly
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
@ttl_cache(seconds=60)  # Quotes change frequently, cache for 1 minute
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
@ttl_cache(seconds=3600)
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
@ttl_cache(seconds=300)  # Candles cached for 5 minutes
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
    if resolution not in SUPPORTED_RESOLUTIONS:
        return {"error": f"Invalid resolution '{resolution}'. Supported: {', '.join(sorted(SUPPORTED_RESOLUTIONS))}"}

    logger.info("Fetching stock candles for %s (res: %s, days: %d)", symbol, resolution, days_back)
    try:
        # Calculate timestamps captures at a single point in time
        now = datetime.now(timezone.utc)
        to_ts = int(now.timestamp())
        from_ts = int((now - timedelta(days=days_back)).timestamp())

        client = get_finnhub_client()
        return client.stock_candles(symbol, resolution, from_ts, to_ts)
    except Exception as e:
        return _create_error_response(f"Failed to fetch stock candles for {symbol}.", e)


@mcp.tool()
@ttl_cache(seconds=600)  # News cached for 10 minutes
def get_company_news(symbol: str, days_back: int = 7) -> list[dict[str, Any]]:
    """Get recent news articles for a specific company.

    Args:
        symbol: The stock ticker symbol.
        days_back: Number of days of news to fetch.

    """
    logger.info("Fetching company news for %s (days_back: %d)", symbol, days_back)
    try:
        now = datetime.now(timezone.utc)
        to_date = now.strftime("%Y-%m-%d")
        from_date = (now - timedelta(days=days_back)).strftime("%Y-%m-%d")

        client = get_finnhub_client()
        return client.company_news(symbol, _from=from_date, to=to_date)
    except Exception as e:
        return _create_error_response(f"Failed to fetch company news for {symbol}.", e)


@mcp.tool()
@ttl_cache(seconds=600)
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
@ttl_cache(seconds=300)
def get_technical_indicators(symbol: str, resolution: str = "D") -> dict[str, Any]:
    """Get aggregate technical indicators (Buy/Sell/Hold signals).

    Args:
        symbol: The stock ticker symbol.
        resolution: Candle resolution. '1', '5', '15', '30', '60', 'D', 'W', 'M'.

    """
    if resolution not in SUPPORTED_RESOLUTIONS:
        return {"error": f"Invalid resolution '{resolution}'. Supported: {', '.join(sorted(SUPPORTED_RESOLUTIONS))}"}

    logger.info("Fetching aggregate indicators for %s (res: %s)", symbol, resolution)
    try:
        client = get_finnhub_client()
        return client.aggregate_indicator(symbol, resolution)
    except Exception as e:
        return _create_error_response(f"Failed to fetch technical indicators for {symbol}.", e)


@mcp.tool()
@ttl_cache(seconds=3600)
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
