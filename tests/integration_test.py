import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pandas as pd
from src.api.kraken_client import KrakenClient

load_dotenv()

@pytest.mark.integration
class TestKrakenIntegration:
    @pytest.fixture
    def kraken_client(self):
        assert os.getenv('KRAKEN_API_KEY') is not None, "KRAKEN_API_KEY not found in environment"
        assert os.getenv('KRAKEN_SECRET_KEY') is not None, "KRAKEN_SECRET_KEY not found in environment"
        return KrakenClient()

    def test_get_ticker_info(self, kraken_client):
        """Test getting real ticker data"""
        try:
            ticker = kraken_client.get_ticker_info("XXBTZUSD")
            assert isinstance(ticker, pd.DataFrame), "Ticker should be a DataFrame"
            assert "XXBTZUSD" in ticker.index, "Expected trading pair not found in ticker data"
            print(f"Received ticker:\n{ticker}")
            assert not ticker.empty, "Ticker DataFrame should not be empty"
        except Exception as e:
            pytest.fail(f"Failed to get ticker info: {str(e)}")