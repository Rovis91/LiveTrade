import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import patch
from src.api.kraken_client import KrakenClient

@pytest.fixture
def kraken_client():
    return KrakenClient()

@patch('src.api.kraken_client.KrakenAPI.get_server_time')
@patch('src.api.kraken_client.KrakenClient.get_account_balance')
def test_test_connection(mock_get_account_balance, mock_get_server_time, kraken_client):
    mock_get_server_time.return_value = {"unixtime": 1629828000}
    mock_get_account_balance.return_value = {"USD": 1000.0}
    
    result = kraken_client.test_connection()
    
    assert result is True
    mock_get_server_time.assert_called_once()
    mock_get_account_balance.assert_called_once()

@patch('src.api.kraken_client.KrakenAPI.get_account_balance')
def test_get_account_balance(mock_get_account_balance, kraken_client):
    mock_get_account_balance.return_value = {"USD": 1000.0}
    
    balance = kraken_client.get_account_balance()
    
    assert balance == {"USD": 1000.0}
    mock_get_account_balance.assert_called_once()

@patch('src.api.kraken_client.KrakenAPI.get_ticker_information')
def test_get_ticker_info(mock_get_ticker_information, kraken_client):
    mock_get_ticker_information.return_value = {"XBTUSD": {"a": ["50000.0"]}}
    
    ticker_info = kraken_client.get_ticker_info("XBTUSD")
    
    assert ticker_info == {"XBTUSD": {"a": ["50000.0"]}}
    mock_get_ticker_information.assert_called_once_with("XBTUSD")

@patch('src.api.kraken_client.KrakenAPI.get_ohlc_data')
def test_get_historical_data(mock_get_ohlc_data, kraken_client):
    mock_get_ohlc_data.return_value = ({"time": [1629828000]}, 12345)
    
    ohlc_data = kraken_client.get_historical_data("XBTUSD", interval=60)
    
    assert "time" in ohlc_data
    mock_get_ohlc_data.assert_called_once_with("XBTUSD", interval=60, since=None)

@patch('src.api.kraken_client.KrakenAPI.add_standard_order')
def test_place_limit_order(mock_add_standard_order, kraken_client):
    mock_add_standard_order.return_value = {"descr": {"order": "buy 0.01 XBTUSD @ limit 30000"}}
    
    order = kraken_client.place_limit_order(pair="XBTUSD", volume=0.01, price=30000, side="buy", validate=True)
    
    assert "descr" in order
    mock_add_standard_order.assert_called_once_with(pair="XBTUSD", type="buy", ordertype="limit", volume=0.01, price=30000, validate=True)

@patch('src.api.kraken_client.API.query_private')
@patch('src.api.kraken_client.KrakenClient.place_limit_order')
def test_update_limit_order(mock_place_limit_order, mock_query_private, kraken_client):
    # Mocking the cancellation response as successful
    mock_query_private.return_value = {"error": [], "result": {"count": 1}}
    
    # Mocking the placement of a new limit order
    mock_place_limit_order.return_value = {"descr": {"order": "buy 0.01 XBTUSD @ limit 31000"}}
    
    # Call the update_limit_order method
    kraken_client.update_limit_order(pair="XBTUSD", volume=0.01, new_price=31000, order_id="order123", side="buy")

    # Asserting that cancel_order (via query_private) and place_limit_order were called
    mock_query_private.assert_called_once_with('CancelOrder', {'txid': 'order123'})
    mock_place_limit_order.assert_called_once_with(pair="XBTUSD", volume=0.01, price=31000, side="buy", validate=False)


@patch('src.api.kraken_client.API.query_private')
def test_cancel_order(mock_query_private, kraken_client):
    mock_query_private.return_value = {"error": [], "result": {"count": 1}}
    
    kraken_client.cancel_order(order_id="order123")
    
    mock_query_private.assert_called_once_with('CancelOrder', {'txid': 'order123'})

@patch('src.api.kraken_client.KrakenAPI.get_open_orders')
def test_get_open_orders(mock_get_open_orders, kraken_client):
    mock_get_open_orders.return_value = {"open": {"order123": {"status": "open"}}}
    
    open_orders = kraken_client.get_open_orders()
    
    assert "open" in open_orders
    mock_get_open_orders.assert_called_once()

@patch('src.api.kraken_client.KrakenAPI.get_trades_history')
def test_get_trade_history(mock_get_trades_history, kraken_client):
    mock_get_trades_history.return_value = {"trades": {"trade123": {"pair": "XBTUSD"}}}
    
    trade_history = kraken_client.get_trade_history()
    
    assert "trades" in trade_history
    mock_get_trades_history.assert_called_once()

@patch('src.api.kraken_client.KrakenAPI.query_orders_info')
def test_get_order_details(mock_query_orders_info, kraken_client):
    mock_query_orders_info.return_value = {"order123": {"status": "closed"}}
    
    order_details = kraken_client.get_order_details(txid="order123")
    
    assert "order123" in order_details
    mock_query_orders_info.assert_called_once_with(txid="order123")

