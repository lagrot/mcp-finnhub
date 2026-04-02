import os
import pytest
from mcp_finnhub.server import get_finnhub_client

def test_get_finnhub_client_no_key():
    """Test that get_finnhub_client raises ValueError when no API key is set."""
    if "FINNHUB_API_KEY" in os.environ:
        del os.environ["FINNHUB_API_KEY"]
    
    with pytest.raises(ValueError, match="FINNHUB_API_KEY environment variable is not set"):
        get_finnhub_client()

def test_get_finnhub_client_with_key():
    """Test that get_finnhub_client returns a client when API key is set."""
    os.environ["FINNHUB_API_KEY"] = "test_key"
    client = get_finnhub_client()
    assert client is not None
    assert client.api_key == "test_key"
