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
    """Get the Finnhub client, initializing it if necessary.

    Returns:
        finnhub.Client: The initialized client.

    Raises:
        ValueError: If FINNHUB_API_KEY is not set and cannot be loaded.

    """
    global _finnhub_client
    if _finnhub_client is None:
        # os.getenv checks system environment variables.
        # load_dotenv() populates these from .env if present.
        api_key = os.getenv("FINNHUB_API_KEY")
        if not api_key:
            error_msg = "FINNHUB_API_KEY environment variable is not set. Please set it in your environment or in a .env file."
            logger.error(error_msg)
            raise ValueError(error_msg)
        try:
            _finnhub_client = finnhub.Client(api_key=api_key)
            logger.info("Finnhub client initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Finnhub client: {e}")
            raise ConnectionError(f"Failed to initialize Finnhub client: {e}") from e
    return _finnhub_client


# Helper function to return MCP-compatible error responses
def _create_error_response(message: str, original_exception: Exception = None) -> dict[str, Any]:
    """Creates a standardized error response dictionary."""
    logger.error(f"Error: {message} - Original Exception: {original_exception}")
    return {"error": message}


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
