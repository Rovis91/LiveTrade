import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import patch, Mock
import pandas as pd
from src.trading.indicators import Indicator

@pytest.fixture
def mock_kraken_client():
    client = Mock()
    df = pd.DataFrame({
        'close': [100.0] * 30  
    })
    client.get_historical_data.return_value = df
    return client

class TestIndicator:
    def test_calculate_sma(self, mock_kraken_client):
        indicator = Indicator(mock_kraken_client)
        sma = indicator.calculate_sma("XXBTZUSD", 60, 25)
        
        assert isinstance(sma, float)
        assert sma == 100.0 
        mock_kraken_client.get_historical_data.assert_called_once_with(
            pair="XXBTZUSD",
            interval=60
        )