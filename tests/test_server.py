from unittest.mock import MagicMock, patch

import os
import pytest
import finnhub  # Import finnhub to use its spec for MagicMock
from mcp_finnhub.server import get_finnhub_client, get_company_profile, get_financial_metrics, get_stock_candles, get_company_news, get_market_news, get_technical_indicators, get_insider_transactions # Import all tools to test

# Mock the finnhub.Client for tool tests
@pytest.fixture
def mock_finnhub_api(monkeypatch):
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
    # Mock for company_insider_transactions
    mock_client.company_insider_transactions.return_value = [
        {"filingDate": "2023-10-26", "transactionDate": "2023-10-25", "insiderName": "Insider One", "insiderTitle": "Director", "transactionType": "buy", "value": 1000000, "shares": 5000},
        {"filingDate": "2023-10-25", "transactionDate": "2023-10-24", "insiderName": "Insider Two", "insiderTitle": "CEO", "transactionType": "sell", "value": 500000, "shares": 2500}
    ]

    # Patch the get_finnhub_client function itself to return our mock client
    # This ensures that when tools call get_finnhub_client(), they get our mock
    with patch('mcp_finnhub.server.get_finnhub_client', return_value=mock_client) as mock_get_client_func:
        yield mock_client, mock_get_client_func

# Existing tests for get_finnhub_client
def test_get_finnhub_client_no_key():
    """Test that get_finnhub_client raises ValueError when no API key is set."""
    if "FINNHUB_API_KEY" in os.environ:
        del os.environ["FINNHUB_API_KEY"]
    
    # Use the actual function for this test
    from mcp_finnhub.server import get_finnhub_client as actual_get_finnhub_client
    
    with pytest.raises(ValueError, match="FINNHUB_API_KEY environment variable is not set"):
        actual_get_finnhub_client()

def test_get_finnhub_client_with_key():
    """Test that get_finnhub_client returns a client when API key is set."""
    os.environ["FINNHUB_API_KEY"] = "test_key"
    
    # Use the actual function for this test
    from mcp_finnhub.server import get_finnhub_client as actual_get_finnhub_client
    
    client = actual_get_finnhub_client()
    assert client is not None
    assert client.api_key == "test_key"
    
    # Clean up env var
    del os.environ["FINNHUB_API_KEY"]

# New tests for tools using the mock_finnhub_api fixture
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

    mock_get_client_func.assert_called_once() # Ensure get_finnhub_client was called
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

def test_get_stock_candles_success(mock_finnhub_api):
    """Test get_stock_candles tool successfully retrieves stock candle data."""
    mock_client, mock_get_client_func = mock_finnhub_api
    expected_candles = {
        "t": [1678886400, 1678972800, 1679059200],
        "o": [150.0, 151.5, 152.0], "h": [152.0, 153.0, 153.5], "l": [149.5, 151.0, 151.8],
        "c": [151.5, 152.5, 153.0], "v": [1000000, 1100000, 1050000], "pc": [149.0, 151.5, 152.5]
    }
    mock_client.stock_candles.return_value = expected_candles

    # Mocking date calculation within server.py is tricky with patch.
    # For this test, we'll assume the date calculation is correct and focus on the call to the client.
    # If we wanted to test date calculation, we'd need to mock datetime.now and timedelta.
    # For now, we'll check the parameters passed to the mocked client.
    
    # We need to know the expected from_ts and to_ts for AAPL with default args.
    # As of April 2, 2026, 30 days back would be around March 3, 2026.
    # Let's use a placeholder like pytest.approx for time-based assertions if needed,
    # or simplify by asserting only the symbol and resolution if date calculation is complex to mock.
    
    # Simplified assertion: check if called and if result matches mock.
    result_default = get_stock_candles(symbol="AAPL")

    mock_get_client_func.assert_called_once()
    # Assert that stock_candles was called. Exact timestamp checks are brittle.
    # We'll rely on the overall result matching the mock for now.
    # If precise timestamp checks were critical, we'd mock datetime.now and timedelta.
    mock_client.stock_candles.assert_called_once() # Check that it was called
    assert result_default == expected_candles

    # Test with custom resolution and days_back
    result_custom = get_stock_candles(symbol="GOOG", resolution="W", days_back=90)
    # In a real scenario, we would calculate expected from_ts and to_ts.
    # For now, we assert the call was made with the correct symbol and resolution.
    mock_client.stock_candles.assert_called_with("GOOG", "W", pytest.raises(Exception), pytest.raises(Exception)) # Checking for parameters
    assert result_custom == expected_candles # This assumes the mock was called again and returned the same value.

def test_get_company_news_success(mock_finnhub_api):
    """Test get_company_news tool successfully retrieves company news."""
    mock_client, mock_get_client_func = mock_finnhub_api
    expected_news = [
        {"id": 1, "datetime": 1679000000, "source": "NewsSource", "headline": "Apple releases new product", "url": "http://example.com/news1"},
        {"id": 2, "datetime": 1678900000, "source": "AnotherSource", "headline": "Analyst upgrades Apple", "url": "http://example.com/news2"}
    ]
    mock_client.company_news.return_value = expected_news

    result = get_company_news(symbol="AAPL")

    mock_get_client_func.assert_called_once()
    # Precise date checks are complex to mock. Asserting call and return value.
    mock_client.company_news.assert_called_once_with("AAPL", _from=pytest.raises(Exception), to=pytest.raises(Exception))
    assert result == expected_news

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

def test_get_insider_transactions_success(mock_finnhub_api):
    """Test get_insider_transactions tool successfully retrieves transactions."""
    mock_client, mock_get_client_func = mock_finnhub_api
    expected_transactions = [
        {"filingDate": "2023-10-26", "transactionDate": "2023-10-25", "insiderName": "Insider One", "insiderTitle": "Director", "transactionType": "buy", "value": 1000000, "shares": 5000},
        {"filingDate": "2023-10-25", "transactionDate": "2023-10-24", "insiderName": "Insider Two", "insiderTitle": "CEO", "transactionType": "sell", "value": 500000, "shares": 2500}
    ]
    mock_client.company_insider_transactions.return_value = expected_transactions

    result = get_insider_transactions(symbol="AAPL")

    mock_get_client_func.assert_called_once()
    mock_client.company_insider_transactions.assert_called_once_with("AAPL")
    assert result == expected_transactions

# Future tests should cover:
# - Error handling for API calls (e.g., invalid symbol, API errors, missing API key caught by tools)
# - Edge cases for parameters (e.g., resolution, days_back)
# - Test the behavior when get_finnhub_client itself raises an error (besides missing key)
