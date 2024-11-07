import sys
import os
from dotenv import load_dotenv
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pandas as pd
import logging
from datetime import datetime, timedelta
from src.api.kraken_client import KrakenClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

def handle_rate_limit():
    """Handle rate limiting by sleeping"""
    time.sleep(5)

@pytest.fixture(scope="module")
def live_client():
    """Create a single client instance for all tests"""
    logger.info("Initializing Kraken client for tests")
    client = KrakenClient()
    assert client.test_connection(), "Failed to connect to Kraken API"
    return client

@pytest.mark.live_api
class TestKrakenLiveAPI:
    def test_server_connection(self, live_client):
        """Verify basic API connectivity"""
        logger.info("Testing server connection")
        assert live_client.test_connection()
        handle_rate_limit()

    def test_get_historical_data(self, live_client):
        """Test OHLC data retrieval"""
        logger.info("Testing historical data retrieval")
        try:
            data = live_client.get_historical_data("EURTUSDT", interval=60)
            logger.info(f"Received data shape: {data.shape}")
            
            # Convert string prices to float
            data['close'] = pd.to_numeric(data['close'], errors='coerce')
            
            # Print first few rows for debugging
            logger.info(f"First few rows of data:\n{data.head()}")
            
            # Validate data structure
            assert isinstance(data, pd.DataFrame), "Should return a DataFrame"
            assert not data.empty, "DataFrame should not be empty"
            
            # Log column names
            logger.info(f"Available columns: {data.columns.tolist()}")
            
            # Validate data types after conversion
            assert pd.api.types.is_numeric_dtype(data['close']), "Close prices should be numeric"
            assert data['close'].min() > 0, "Prices should be positive"
            
            handle_rate_limit()
            
        except Exception as e:
            logger.error(f"Error in historical data test: {str(e)}")
            raise

    def test_get_ticker_info_structure(self, live_client):
        """Test ticker data structure and content"""
        logger.info("Testing ticker info structure")
        try:
            ticker = live_client.get_ticker_info("EURTUSDT")
            logger.info(f"Received ticker data:\n{ticker}")
            
            assert isinstance(ticker, pd.DataFrame), "Should return a DataFrame"
            assert "EURTUSDT" in ticker.index, "EURTUSDT not found in ticker data"
            
            handle_rate_limit()
                
        except Exception as e:
            logger.error(f"Error in ticker info test: {str(e)}")
            raise

    def test_get_multiple_tickers(self, live_client):
        """Test retrieving multiple trading pairs"""
        logger.info("Testing multiple ticker retrieval")
        pairs = ["EURTUSDT", "XETHZUSD"]
        
        for pair in pairs:
            logger.info(f"Retrieving ticker for {pair}")
            try:
                ticker = live_client.get_ticker_info(pair)
                logger.info(f"Received ticker for {pair}")
                assert isinstance(ticker, pd.DataFrame)
                assert pair in ticker.index, f"Pair {pair} not found in ticker data"
                handle_rate_limit()
            except Exception as e:
                logger.error(f"Error retrieving ticker for {pair}: {str(e)}")
                raise

    def test_get_account_balance_structure(self, live_client):
        """Test account balance data structure (no amount validation)"""
        logger.info("Testing account balance structure")
        try:
            balance = live_client.get_account_balance()
            logger.info(f"Received balance data: {balance}")
            
            # Convert DataFrame to dict if necessary
            if isinstance(balance, pd.DataFrame):
                balance = balance.to_dict('index')
            
            assert isinstance(balance, dict), "Balance should be a dictionary"
            
            # Log the currencies found
            logger.info(f"Found currencies: {list(balance.keys())}")
            
            # If balance is empty, that's okay - just log it
            if not balance:
                logger.info("No balance data found - this is expected for API keys with read-only access")
                
            handle_rate_limit()
                
        except Exception as e:
            logger.error(f"Error in account balance test: {str(e)}")
            raise

    def test_error_handling(self, live_client):
        """Test API error handling with invalid inputs"""
        logger.info("Testing error handling with invalid trading pair")
        
        # Test invalid pair
        invalid_pair = "INVALID"
        with pytest.raises(ValueError) as exc_info:
            live_client.get_ticker_info(invalid_pair)
        
        error_msg = str(exc_info.value)
        logger.info(f"Received expected error: {error_msg}")
        assert "Unknown trading pair" in error_msg or "Kraken API error" in error_msg
        
        handle_rate_limit()
        
        # Test with empty string
        with pytest.raises(ValueError) as exc_info:
            live_client.get_ticker_info("")
        assert "Invalid trading pair format" in str(exc_info.value)
        
        handle_rate_limit()
    
