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
    """Get the Finnhub client, prioritizing non-placeholder system keys.
    
    This function uses a robust, multi-step verification to ensure a valid
    API key is found and that it actually works with the Finnhub API.
    """
    global _finnhub_client
    if _finnhub_client is not None:
        return _finnhub_client

    # Define common placeholder strings that should be ignored
    PLACEHOLDERS = ["YOUR_API_KEY", "your_api_key", "placeholder"]

    def is_valid_key(key: str | None) -> bool:
        """Checks if a key string is non-empty and not a known placeholder."""
        if not key or not isinstance(key, str):
            return False
        key_lower = key.lower()
        return not any(p.lower() in key_lower for p in PLACEHOLDERS)

    # Step 1: Check existing system environment
    api_key = os.environ.get("FINNHUB_API_KEY")
    origin = "system environment"

    # Step 2: If no valid key in environment, try loading from .env
    if not is_valid_key(api_key):
        load_dotenv()
        # Re-check environment after load_dotenv()
        api_key = os.environ.get("FINNHUB_API_KEY")
        origin = ".env file"

    # Step 3: Final validation check before attempting API connection
    if not is_valid_key(api_key):
        error_msg = (
            f"FINNHUB_API_KEY is missing or invalid. Found '{api_key}' from {origin}. "
            "Please export a valid key in your shell or update your .env file."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Step 4: Proactive verification. A 'valid' looking key might still be 401/403.
    try:
        # We strip potential whitespace/quotes to be safe
        api_key = api_key.strip("'\" ")
        client = finnhub.Client(api_key=api_key)
        
        # Real-world verification: Attempt a lightweight call (AAPL profile)
        client.company_profile2(symbol="AAPL")
        
        # If we reached here, the key is fully functional
        _finnhub_client = client
        logger.info(f"Finnhub client successfully initialized using {origin} (Key: {api_key[:4]}...)")
        return _finnhub_client

    except Exception as e:
        status_code = getattr(e, 'status_code', None)
        msg = f"Finnhub API validation failed using {origin}. "
        
        if status_code == 401:
            msg += f"The key '{api_key[:4]}...' was rejected (401 Unauthorized)."
        elif status_code == 403:
            msg += f"Access denied for '{api_key[:4]}...' (403 Forbidden). You may need a paid plan for some tools."
        else:
            msg += f"Unexpected error: {e}"
            
        logger.error(msg)
        raise ConnectionError(msg) from e


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
    except ValueError as e: # Specifically catch missing API key error
        return _create_error_response(str(e))
    except Exception as e: # Catch other Finnhub API or connection errors
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
    except ValueError as e:
        return _create_error_response(str(e))
    except Exception as e:
        return _create_error_response(f"Failed to fetch financial metrics for {symbol}.", e)


@mcp.tool()
def get_stock_candles(
    symbol: str,
    resolution: str = "D",
    days_back: int = 30,
) -> dict[str, Any]:
    """Get historical stock price data (OHLCV).

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
    except ValueError as e:
        return _create_error_response(str(e))
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
    except ValueError as e:
        return _create_error_response(str(e))
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
    except ValueError as e:
        return _create_error_response(str(e))
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
    except ValueError as e:
        return _create_error_response(str(e))
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
    except ValueError as e:
        return _create_error_response(str(e))
    except Exception as e:
        return _create_error_response(f"Failed to fetch insider transactions for {symbol}.", e)


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
