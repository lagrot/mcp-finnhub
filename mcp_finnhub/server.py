import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import finnhub
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables for local development
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
        ValueError: If FINNHUB_API_KEY is not set.

    """
    global _finnhub_client
    if _finnhub_client is None:
        api_key = os.getenv("FINNHUB_API_KEY")
        if not api_key:
            error_msg = "FINNHUB_API_KEY environment variable is not set"
            logger.error(error_msg)
            raise ValueError(error_msg)
        _finnhub_client = finnhub.Client(api_key=api_key)
    return _finnhub_client


@mcp.tool()
def get_company_profile(symbol: str) -> dict[str, Any]:
    """Get basic company information (name, ticker, industry, market cap, etc.).

    Args:
        symbol: The stock ticker symbol (e.g., AAPL, TSLA).

    """
    logger.info("Fetching company profile for %s", symbol)
    return get_finnhub_client().company_profile2(symbol=symbol)


@mcp.tool()
def get_financial_metrics(symbol: str) -> dict[str, Any]:
    """Get key financial ratios and metrics (P/E, margins, growth, etc.).

    Args:
        symbol: The stock ticker symbol (e.g., AAPL).

    """
    logger.info("Fetching basic financials for %s", symbol)
    return get_finnhub_client().company_basic_financials(symbol, "all")


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
    to_ts = int(datetime.now(timezone.utc).timestamp())
    from_ts = int((datetime.now(timezone.utc) - timedelta(days=days_back)).timestamp())

    logger.info(
        "Fetching stock candles for %s (res: %s, days: %d)",
        symbol,
        resolution,
        days_back,
    )
    return get_finnhub_client().stock_candles(symbol, resolution, from_ts, to_ts)


@mcp.tool()
def get_company_news(symbol: str, days_back: int = 7) -> list[dict[str, Any]]:
    """Get recent news articles for a specific company.

    Args:
        symbol: The stock ticker symbol.
        days_back: Number of days of news to fetch.

    """
    to_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    from_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime(
        "%Y-%m-%d",
    )

    logger.info(
        "Fetching company news for %s from %s to %s",
        symbol,
        from_date,
        to_date,
    )
    return get_finnhub_client().company_news(symbol, _from=from_date, to=to_date)


@mcp.tool()
def get_market_news(category: str = "general") -> list[dict[str, Any]]:
    """Get general market news.

    Args:
        category: News category. 'general', 'forex', 'crypto', 'merger'.

    """
    logger.info("Fetching general news for category: %s", category)
    return get_finnhub_client().general_news(category, min_id=0)


@mcp.tool()
def get_technical_indicators(symbol: str, resolution: str = "D") -> dict[str, Any]:
    """Get aggregate technical indicators (Buy/Sell/Hold signals).

    Args:
        symbol: The stock ticker symbol.
        resolution: Candle resolution. '1', '5', '15', '30', '60', 'D', 'W', 'M'.

    """
    logger.info("Fetching aggregate indicators for %s (res: %s)", symbol, resolution)
    return get_finnhub_client().aggregate_indicator(symbol, resolution)


@mcp.tool()
def get_insider_transactions(symbol: str) -> dict[str, Any]:
    """Get recent insider transactions for a company.

    Args:
        symbol: The stock ticker symbol.

    """
    logger.info("Fetching insider transactions for %s", symbol)
    # Note: Depending on the API plan, this might be limited.
    return get_finnhub_client().company_insider_transactions(symbol)


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
