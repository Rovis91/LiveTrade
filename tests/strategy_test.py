import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import patch, Mock
from src.trading.strategy import LimitStrategy


@pytest.fixture
def mock_config():
    return {
        "pair": "XXBTZUSD",
        "timeframe": "1h",
        "sma_length": 25,
        "depeg_percentage": 4,
        "volume": 0.001,
        "base_currency": "ZUSD",
        "check_interval": 3
    }

@pytest.fixture
def mock_kraken_client():
    client = Mock()
    client.get_account_balance.return_value = {"ZUSD": 1000.0}
    client.get_historical_data.return_value = {"close": [100.0] * 26}
    client.get_ticker_info.return_value = {"XXBTZUSD": {"c": ["30000.0"]}}
    return client

@pytest.fixture
def mock_indicator():
    indicator = Mock()
    indicator.calculate_sma.return_value = 100.0
    return indicator

class TestLimitStrategy:
    def test_init(self, mock_config, mock_kraken_client, mock_indicator):
        strategy = LimitStrategy(mock_config, mock_kraken_client, mock_indicator)
        assert strategy.test_mode == True
        assert strategy.active_order is None
        assert strategy.in_position == False

    def test_calculate_target_price(self, mock_config, mock_kraken_client, mock_indicator):
        strategy = LimitStrategy(mock_config, mock_kraken_client, mock_indicator)
        target_price = strategy.calculate_target_price()
        expected_price = 96.0  # 100 * (1 - 4/100)
        assert target_price == expected_price

    def test_check_balance_for_order(self, mock_config, mock_kraken_client, mock_indicator):
        strategy = LimitStrategy(mock_config, mock_kraken_client, mock_indicator, test_mode=False)
        strategy.calculate_target_price = Mock(return_value=30000.0)
        result = strategy.check_balance_for_order()
        assert result == True
        mock_kraken_client.get_account_balance.assert_called_once()

    @patch('src.trading.strategy.logger')
    def test_execute_buy_order(self, mock_logger, mock_config, mock_kraken_client, mock_indicator):
        strategy = LimitStrategy(mock_config, mock_kraken_client, mock_indicator)
        mock_kraken_client.place_limit_order.return_value = {"txid": ["123"]}
        
        strategy.execute()
        mock_kraken_client.place_limit_order.assert_called_once()