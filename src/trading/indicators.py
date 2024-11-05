import logging
from typing import Any

logger = logging.getLogger(__name__)

class Indicator:
    """
    Technical analysis indicator calculations.
    Currently supports SMA calculation using Kraken OHLC data.
    """
    
    def __init__(self, kraken_client: Any) -> None:
        """
        Initialize the indicator calculator.

        Args:
            kraken_client: Instance of KrakenClient for data retrieval
        """
        self.client = kraken_client

    def calculate_sma(self, pair: str, timeframe: int, length: int) -> float:
        """
        Calculate Simple Moving Average for the specified pair and parameters.

        Args:
            pair: Trading pair symbol (e.g., 'XXBTZUSD')
            timeframe: Candle timeframe in minutes
            length: Number of periods for SMA calculation

        Returns:
            float: Calculated SMA value

        Raises:
            Exception: If data retrieval or calculation fails
        """
        try:
            # Get historical data
            ohlc_data = self.client.get_historical_data(
                pair=pair,
                interval=timeframe
            )

            # Calculate SMA using closing prices
            sma = ohlc_data['close'].rolling(window=length).mean().iloc[-1]
            logger.info(f"Calculated SMA{length}: {sma}")
            
            return float(sma)
            
        except Exception as e:
            logger.error(f"Error calculating SMA for {pair}: {str(e)}")
            raise