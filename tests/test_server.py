from unittest.mock import MagicMock, patch
import datetime # Import datetime to mock it
import time

import os
import pytest
import finnhub  # Import finnhub to use its spec for MagicMock
from mcp_finnhub.server import (
    get_finnhub_client, get_company_profile, get_financial_metrics, 
    get_stock_candles, get_company_news, get_market_news, 
    get_technical_indicators, get_insider_transactions, get_quote, 
    get_recommendation_trends
)

# Mock the finnhub.Client for tool tests
@pytest.fixture
def mock_finnhub_api():
    """
    Fixture to mock the finnhub.Client and its methods.
    It patches the get_finnhub_client function to return a mock client.
    """
    mock_client = MagicMock(spec=finnhub.Client)
    
    # Mock specific methods that tools call
    mock_client.company_profile2.return_value = {
        "symbol": "AAPL", "price": 170.0, "currency": "USD", "exchange": "NASDAQ",
        "name": "Apple Inc.", "ipo": "1980-12-12", "industry": "Technology",
        "marketCapitalization": 2800000000000, "url": "https://www.apple.com"
    }
    # Mock for quote
    mock_client.quote.return_value = {
        "c": 255.94, "d": 0.31, "dp": 0.1213, "h": 256.13, "l": 250.65, "o": 254.21, "pc": 255.63, "t": 1775160000
    }
    # Mock for recommendation_trends
    mock_client.recommendation_trends.return_value = [
        {"buy": 23, "hold": 15, "period": "2026-04-01", "sell": 2, "strongBuy": 14, "strongSell": 0, "symbol": "AAPL"}
    ]
    mock_client.company_basic_financials.return_value = {
        "symbol": "AAPL",
        "financials": [
            {
                "statement": "bs", # balance sheet
                "period": "2023-09-30",
                "data": [{"accountsPayable": 110000000000, "accountsReceivable": 50000000000, "asList": 123456789, "auditFees": 5000000, "buildingsAndEquipmentsNet": 150000000000, "cashAndCashEquivalents": 100000000000}]
            },
            {
                "statement": "is", # income statement
                "period": "2023-09-30",
                "data": [{"costAndSales": 383000000000, "depreciationAndAmortization": 11000000000, "ebit": 100000000000, "ebitda": 120000000000, "grossProfit": 169000000000}]
            }
        ]
    }
    # Mock for stock_candles
    mock_client.stock_candles.return_value = {
        "t": [1678886400, 1678972800, 1679059200], # Timestamps
        "o": [150.0, 151.5, 152.0], # Open
        "h": [152.0, 153.0, 153.5], # High
        "l": [149.5, 151.0, 151.8], # Low
        "c": [151.5, 152.5, 153.0], # Close
        "v": [1000000, 1100000, 1050000], # Volume
        "pc": [149.0, 151.5, 152.5] # Previous Close
    }
    # Mock for company_news
    mock_client.company_news.return_value = [
        {"id": 1, "datetime": 1679000000, "source": "NewsSource", "headline": "Apple releases new product", "url": "http://example.com/news1"},
        {"id": 2, "datetime": 1678900000, "source": "AnotherSource", "headline": "Analyst upgrades Apple", "url": "http://example.com/news2"}
    ]
    # Mock for general_news
    mock_client.general_news.return_value = [
        {"id": 101, "datetime": 1679000000, "source": "MarketNews", "headline": "Market update", "url": "http://example.com/marketnews1"},
        {"id": 102, "datetime": 1678900000, "source": "GlobalNews", "headline": "Economy trends", "url": "http://example.com/marketnews2"}
    ]
    # Mock for aggregate_indicator
    mock_client.aggregate_indicator.return_value = {
        "symbol": "AAPL", "resolution": "D",
        "technicalAnalysis": {"signal": {"movingAverage": "Buy", "macd": "Sell", "rsi": "Hold"}, "oscillator": "Buy"}
    }
    # Corrected method name and structure for insider transactions
    mock_client.stock_insider_transactions.return_value = {
        "symbol": "AAPL",
        "data": [
            {"filingDate": "2023-10-26", "transactionDate": "2023-10-25", "insiderName": "Insider One", "insiderTitle": "Director", "transactionType": "buy", "value": 1000000, "shares": 5000},
            {"filingDate": "2023-10-25", "transactionDate": "2023-10-24", "insiderName": "Insider Two", "insiderTitle": "CEO", "transactionType": "sell", "value": 500000, "shares": 2500}
        ]
    }

    # Patch the get_finnhub_client function itself to return our mock client
    with patch('mcp_finnhub.server.get_finnhub_client', return_value=mock_client) as mock_get_client_func:
        yield mock_client, mock_get_client_func

# Existing tests for get_finnhub_client
def test_get_finnhub_client_no_key():
    """Test that get_finnhub_client raises ValueError when no API key is set."""
    # Reset the global client to force re-initialization
    import mcp_finnhub.server
    mcp_finnhub.server._finnhub_client = None
    
    # Temporarily remove key and prevent .env loading from finding it
    with patch.dict(os.environ, clear=True):
        # We also need to patch load_dotenv to do nothing so it doesn't find the real .env
        with patch('mcp_finnhub.server.load_dotenv'):
            from mcp_finnhub.server import get_finnhub_client as actual_get_finnhub_client
            with pytest.raises(ValueError, match="FINNHUB_API_KEY is missing or invalid"):
                actual_get_finnhub_client()

def test_get_finnhub_client_with_key():
    """Test that get_finnhub_client returns a client when API key is set."""
    # Reset the global client
    import mcp_finnhub.server
    mcp_finnhub.server._finnhub_client = None
    
    test_key = "valid_test_key_not_placeholder"
    
    with patch.dict(os.environ, {"FINNHUB_API_KEY": test_key}):
        from mcp_finnhub.server import get_finnhub_client as actual_get_finnhub_client
        # Mock the verification call inside get_finnhub_client
        with patch('finnhub.Client.company_profile2', return_value={}):
            client = actual_get_finnhub_client()
            assert client is not None
            assert client.api_key == test_key

# New tests for tools using the mock_finnhub_api fixture
@patch('mcp_finnhub.server.datetime') # Patch datetime module
@patch('mcp_finnhub.server.timedelta') # Patch timedelta module
def test_get_stock_candles_success(mock_timedelta, mock_datetime, mock_finnhub_api):
    """Test get_stock_candles tool successfully retrieves stock candle data, including date calculations."""
    mock_client, mock_get_client_func = mock_finnhub_api
    
    expected_candles = {
        "t": [1678886400, 1678972800, 1679059200],
        "o": [150.0, 151.5, 152.0], "h": [152.0, 153.0, 153.5], "l": [149.5, 151.0, 151.8],
        "c": [151.5, 152.5, 153.0], "v": [1000000, 1100000, 1050000], "pc": [149.0, 151.5, 152.5]
    }
    mock_client.stock_candles.return_value = expected_candles

    # Mock datetime.now() and timedelta() to control date calculations
    mock_now = datetime.datetime(2026, 4, 2, 12, 0, 0, tzinfo=datetime.timezone.utc)
    mock_delta = datetime.timedelta(days=30)
    mock_datetime.now.return_value = mock_now
    # This mock setup allows timedelta(days=...) to return a mock timedelta object
    mock_timedelta.side_effect = lambda days: datetime.timedelta(days=days) 

    # Calculate expected timestamps based on mock_now and mock_delta
    expected_to_ts = int(mock_now.timestamp())
    expected_from_ts = int((mock_now - mock_delta).timestamp())

    result_default = get_stock_candles(symbol="AAPL")

    mock_get_client_func.assert_called_once()
    # Assert that stock_candles was called with the correct parameters, including calculated timestamps
    mock_client.stock_candles.assert_called_once_with("AAPL", "D", expected_from_ts, expected_to_ts)
    assert result_default == expected_candles

def test_get_stock_candles_invalid_resolution(mock_finnhub_api):
    """Test get_stock_candles returns error for invalid resolution."""
    result = get_stock_candles(symbol="AAPL", resolution="INVALID")
    assert "error" in result
    assert "Invalid resolution" in result["error"]

@patch('mcp_finnhub.server.datetime') # Patch datetime module
def test_get_company_news_success(mock_datetime, mock_finnhub_api):
    """Test get_company_news tool successfully retrieves company news, including date calculations."""
    mock_client, mock_get_client_func = mock_finnhub_api
    expected_news = [
        {"id": 1, "datetime": 1679000000, "source": "NewsSource", "headline": "Apple releases new product", "url": "http://example.com/news1"},
        {"id": 2, "datetime": 1678900000, "source": "AnotherSource", "headline": "Analyst upgrades Apple", "url": "http://example.com/news2"}
    ]
    mock_client.company_news.return_value = expected_news

    # Mock datetime.now() to control date calculations
    mock_now = datetime.datetime(2026, 4, 2, 12, 0, 0, tzinfo=datetime.timezone.utc)
    mock_datetime.now.return_value = mock_now
    # Mock timedelta for days_back calculation
    # Ensure mock_datetime.timedelta can be called to return our mock instance
    mock_datetime.timedelta.side_effect = lambda days: datetime.timedelta(days=days)

    # Calculate expected dates based on mock_now and mock_timedelta
    expected_to_date = mock_now.strftime("%Y-%m-%d")
    expected_from_date = (mock_now - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    
    result = get_company_news(symbol="AAPL")

    mock_get_client_func.assert_called_once()
    # Assert that company_news was called with the correctly formatted dates
    mock_client.company_news.assert_called_once_with("AAPL", _from=expected_from_date, to=expected_to_date)
    assert result == expected_news

def test_get_company_profile_success(mock_finnhub_api):
    """Test get_company_profile tool successfully retrieves company data."""
    mock_client, mock_get_client_func = mock_finnhub_api
    expected_profile = {
        "symbol": "AAPL", "price": 170.0, "currency": "USD", "exchange": "NASDAQ",
        "name": "Apple Inc.", "ipo": "1980-12-12", "industry": "Technology",
        "marketCapitalization": 2800000000000, "url": "https://www.apple.com"
    }
    mock_client.company_profile2.return_value = expected_profile

    result = get_company_profile(symbol="AAPL")

    mock_get_client_func.assert_called_once()
    mock_client.company_profile2.assert_called_once_with(symbol="AAPL")
    assert result == expected_profile

def test_get_financial_metrics_success(mock_finnhub_api):
    """Test get_financial_metrics tool successfully retrieves financial data."""
    mock_client, mock_get_client_func = mock_finnhub_api
    expected_metrics = {
        "symbol": "AAPL",
        "financials": [
            {
                "statement": "bs",
                "period": "2023-09-30",
                "data": [{"accountsPayable": 110000000000, "accountsReceivable": 50000000000, "asList": 123456789, "auditFees": 5000000, "buildingsAndEquipmentsNet": 150000000000, "cashAndCashEquivalents": 100000000000}]
            },
            {
                "statement": "is",
                "period": "2023-09-30",
                "data": [{"costAndSales": 383000000000, "depreciationAndAmortization": 11000000000, "ebit": 100000000000, "ebitda": 120000000000, "grossProfit": 169000000000}]
            }
        ]
    }
    mock_client.company_basic_financials.return_value = expected_metrics

    result = get_financial_metrics(symbol="AAPL")

    mock_get_client_func.assert_called_once()
    mock_client.company_basic_financials.assert_called_once_with("AAPL", "all")
    assert result == expected_metrics

def test_get_market_news_success(mock_finnhub_api):
    """Test get_market_news tool successfully retrieves general market news."""
    mock_client, mock_get_client_func = mock_finnhub_api
    expected_news = [
        {"id": 101, "datetime": 1679000000, "source": "MarketNews", "headline": "Market update", "url": "http://example.com/marketnews1"},
        {"id": 102, "datetime": 1678900000, "source": "GlobalNews", "headline": "Economy trends", "url": "http://example.com/marketnews2"}
    ]
    mock_client.general_news.return_value = expected_news

    result = get_market_news(category="general")

    mock_get_client_func.assert_called_once()
    mock_client.general_news.assert_called_once_with("general", min_id=0)
    assert result == expected_news

def test_get_technical_indicators_success(mock_finnhub_api):
    """Test get_technical_indicators tool successfully retrieves indicators."""
    mock_client, mock_get_client_func = mock_finnhub_api
    expected_indicators = {
        "symbol": "AAPL", "resolution": "D",
        "technicalAnalysis": {"signal": {"movingAverage": "Buy", "macd": "Sell", "rsi": "Hold"}, "oscillator": "Buy"}
    }
    mock_client.aggregate_indicator.return_value = expected_indicators

    result = get_technical_indicators(symbol="AAPL", resolution="D")

    mock_get_client_func.assert_called_once()
    mock_client.aggregate_indicator.assert_called_once_with("AAPL", "D")
    assert result == expected_indicators

def test_get_technical_indicators_invalid_resolution(mock_finnhub_api):
    """Test get_technical_indicators returns error for invalid resolution."""
    result = get_technical_indicators(symbol="AAPL", resolution="INVALID")
    assert "error" in result
    assert "Invalid resolution" in result["error"]

def test_get_insider_transactions_success(mock_finnhub_api):
    """Test get_insider_transactions tool successfully retrieves transactions."""
    mock_client, mock_get_client_func = mock_finnhub_api
    expected_transactions = {
        "symbol": "AAPL",
        "data": [
            {"filingDate": "2023-10-26", "transactionDate": "2023-10-25", "insiderName": "Insider One", "insiderTitle": "Director", "transactionType": "buy", "value": 1000000, "shares": 5000},
            {"filingDate": "2023-10-25", "transactionDate": "2023-10-24", "insiderName": "Insider Two", "insiderTitle": "CEO", "transactionType": "sell", "value": 500000, "shares": 2500}
        ]
    }
    mock_client.stock_insider_transactions.return_value = expected_transactions

    result = get_insider_transactions(symbol="AAPL")

    mock_get_client_func.assert_called_once()
    mock_client.stock_insider_transactions.assert_called_once_with("AAPL")
    assert result == expected_transactions

def test_get_quote_success(mock_finnhub_api):
    """Test get_quote tool successfully retrieves quote data."""
    mock_client, mock_get_client_func = mock_finnhub_api
    expected_quote = {
        "c": 255.94, "d": 0.31, "dp": 0.1213, "h": 256.13, "l": 250.65, "o": 254.21, "pc": 255.63, "t": 1775160000
    }
    mock_client.quote.return_value = expected_quote

    result = get_quote(symbol="AAPL")

    mock_get_client_func.assert_called_once()
    mock_client.quote.assert_called_once_with("AAPL")
    assert result == expected_quote

def test_get_recommendation_trends_success(mock_finnhub_api):
    """Test get_recommendation_trends tool successfully retrieves data."""
    mock_client, mock_get_client_func = mock_finnhub_api
    expected_trends = [
        {"buy": 23, "hold": 15, "period": "2026-04-01", "sell": 2, "strongBuy": 14, "strongSell": 0, "symbol": "AAPL"}
    ]
    mock_client.recommendation_trends.return_value = expected_trends

    result = get_recommendation_trends(symbol="AAPL")

    mock_get_client_func.assert_called_once()
    mock_client.recommendation_trends.assert_called_once_with("AAPL")
    assert result == expected_trends

def test_caching_logic(mock_finnhub_api):
    """Test that the caching layer works by calling a tool twice and verifying only one client call."""
    mock_client, mock_get_client_func = mock_finnhub_api
    
    # Use a unique symbol to avoid interference with other tests if the cache is persistent
    test_symbol = "CACHE-TEST"
    
    # First call - should trigger get_finnhub_client and API call
    get_quote(symbol=test_symbol)
    assert mock_get_client_func.call_count == 1
    
    # Second call - should be a cache hit, so NO new calls to get_finnhub_client or mock_client
    get_quote(symbol=test_symbol)
    assert mock_get_client_func.call_count == 1
    mock_client.quote.assert_called_once_with(test_symbol)
