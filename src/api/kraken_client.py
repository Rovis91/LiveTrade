import os
from typing import Dict, Any, Optional
from krakenex import API
from pykrakenapi import KrakenAPI
from dotenv import load_dotenv
import logging
import pandas as pd

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("kraken_client")


class KrakenClient:
    def __init__(self, api: Optional[API] = None):
        """
        Initialize the KrakenClient with API credentials from environment variables or an existing API instance.
        
        Args:
            api (Optional[API]): An optional Kraken API instance for dependency injection (primarily for testing).
        """
        if api is None:
            api = API(
                key=os.getenv('KRAKEN_API_KEY'),
                secret=os.getenv('KRAKEN_SECRET_KEY')
            )
        
        self.api = api
        self.kraken = KrakenAPI(api)
        logger.info("Kraken client initialized")

    def test_connection(self) -> bool:
        """
        Test API connection and key validity.
        
        Returns:
            bool: True if the connection and keys are valid, False otherwise.
        """
        try:
            # Get server time to test public API
            self.kraken.get_server_time()
            
            # Get account balance to test private API
            self.get_account_balance()
            
            logger.info("API connection test successful")
            return True
        except Exception as e:
            logger.error(f"API connection test failed: {str(e)}")
            return False

    def get_account_balance(self) -> Dict[str, float]:
        """
        Get account balance as a dictionary.

        Returns:
            Dict[str, float]: A dictionary of account balances by currency.
        """
        try:
            balance = self.kraken.get_account_balance()
            # Convert DataFrame to dict if necessary
            if isinstance(balance, pd.DataFrame):
                balance = balance.to_dict('index')
            logger.info("Account balance retrieved successfully")
            return balance
        except Exception as e:
            logger.error(f"Error getting account balance: {str(e)}")
            raise

    def get_ticker_info(self, pair: str) -> pd.DataFrame:
        """
        Get current ticker information for a trading pair.
        
        Args:
            pair (str): The currency pair (e.g., "EURTUSDT")
        
        Returns:
            pd.DataFrame: Ticker information for the specified pair
            
        Raises:
            ValueError: If the pair is invalid or not found
        """
        try:
            if not isinstance(pair, str) or len(pair) < 3:
                raise ValueError(f"Invalid trading pair format: {pair}")
                
            response = self.api.query_public('Ticker', {'pair': pair})
            if 'error' in response and response['error']:
                raise ValueError(f"Kraken API error: {response['error'][0]}")
                
            ticker = self.kraken.get_ticker_information(pair)
            logger.info(f"Ticker info retrieved for {pair}")
            return ticker
        except Exception as e:
            error_msg = str(e)
            if 'EQuery:Unknown asset pair' in error_msg:
                raise ValueError(f"Unknown trading pair: {pair}")
            logger.error(f"Error getting ticker info: {error_msg}")
            raise
        
    def get_historical_data(self, pair: str, interval: int = 60, since: Optional[int] = None) -> pd.DataFrame:
        """
        Get historical OHLC data for a given trading pair.
        
        Args:
            pair (str): The currency pair (e.g., "XBTUSD").
            interval (int): Timeframe interval in minutes. Default is 60 (1 hour).
            since (Optional[int]): Optional timestamp for data retrieval.
        
        Returns:
            pd.DataFrame: Historical OHLC data.
        """
        try:
            ohlc, _ = self.kraken.get_ohlc_data(pair, interval=interval, since=since)
            logger.info(f"Historical data retrieved for {pair}")
            return ohlc
        except Exception as e:
            logger.error(f"Error getting historical data for {pair}: {str(e)}")
            raise

    def place_limit_order(self, pair: str, volume: float, price: float, side: str = "buy", validate: bool = True) -> Dict[str, Any]:
        """
        Place a limit order.
        
        Args:
            pair (str): The trading pair (e.g., "XBTUSD").
            volume (float): The amount to buy or sell.
            price (float): The limit price.
            side (str): "buy" or "sell".
            validate (bool): Whether to validate without actually placing the order (for testing).
        
        Returns:
            Dict[str, Any]: Response from Kraken API.
        """
        try:
            order = self.kraken.add_standard_order(
                pair=pair,
                type=side,
                ordertype='limit',
                volume=volume,
                price=price,
                validate=validate
            )
            if validate:
                logger.info(f"Validated limit order: {order}")
            else:
                logger.info(f"Limit order placed: {order}")
            return order
        except Exception as e:
            logger.error(f"Error placing limit order for {pair}: {str(e)}")
            raise

    def cancel_order(self, order_id: str) -> None:
        """
        Cancel an active order.
        
        Args:
            order_id (str): The ID of the order to cancel.
        """
        try:
            response = self.api.query_private('CancelOrder', {'txid': order_id})
            if response.get("error"):
                logger.error(f"Error canceling order {order_id}: {response['error']}")
                raise Exception(response['error'])
            logger.info(f"Order {order_id} canceled successfully.")
        except Exception as e:
            logger.error(f"Error canceling order {order_id}: {str(e)}")
            raise

    def get_open_orders(self) -> Dict[str, Any]:
        """
        Retrieve all open orders for the account.
        
        Returns:
            Dict[str, Any]: A dictionary containing open orders.
        """
        try:
            open_orders = self.kraken.get_open_orders()
            logger.info("Open orders retrieved successfully.")
            return open_orders
        except Exception as e:
            logger.error(f"Error retrieving open orders: {str(e)}")
            raise

    def get_trade_history(self) -> Dict[str, Any]:
        """
        Retrieve trade history for the account.
        
        Returns:
            Dict[str, Any]: A dictionary containing the trade history.
        """
        try:
            trades = self.kraken.get_trades_history()
            logger.info("Trade history retrieved successfully.")
            return trades
        except Exception as e:
            logger.error(f"Error retrieving trade history: {str(e)}")
            raise

    def get_order_details(self, txid: str) -> Dict[str, Any]:
        """
        Get details of a specific order.
        
        Args:
            txid (str): The transaction ID of the order.
        
        Returns:
            Dict[str, Any]: A dictionary containing the order details.
        """
        try:
            order_details = self.kraken.query_orders_info(txid=txid)
            logger.info(f"Order details retrieved for transaction ID {txid}.")
            return order_details
        except Exception as e:
            logger.error(f"Error retrieving order details for transaction ID {txid}: {str(e)}")
            raise

    def update_limit_order(self, pair: str, volume: float, new_price: float, order_id: str, side: str) -> None:
        """
        Update an existing limit order by canceling it and placing a new one.
        
        Args:
            pair (str): The trading pair (e.g., "XBTUSD").
            volume (float): The volume of the new order.
            new_price (float): The new price for the limit order.
            order_id (str): The ID of the order to update.
            side (str): "buy" or "sell".
        """
        try:
            # Cancel the existing order
            self.cancel_order(order_id)

            # Place a new order with updated details
            self.place_limit_order(pair=pair, volume=volume, price=new_price, side=side, validate=False)
            logger.info(f"Order updated for {pair} to new price {new_price}")
        except Exception as e:
            logger.error(f"Error updating limit order for {pair}: {str(e)}")
            raise