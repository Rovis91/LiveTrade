import json
import time
import signal
import logging
from typing import Optional
from pathlib import Path

from src.api.kraken_client import KrakenClient
from src.trading.indicators import Indicator
from src.trading.strategy import LimitStrategy

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global flag for shutdown
running = True

def load_config() -> dict:
    """Load trading configuration from JSON file."""
    config_path = Path("config/trading_config.json")
    try:
        with open(config_path) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise

def handle_shutdown(strategy: Optional[LimitStrategy] = None) -> None:
    """Handle graceful shutdown of the bot."""
    global running
    running = False
    logger.info("Shutting down bot...")
    if strategy and not strategy.test_mode and strategy.active_order:
        try:
            strategy.client.cancel_order(strategy.active_order)
            logger.info("Cancelled open orders")
        except Exception as e:
            logger.error(f"Error cancelling orders during shutdown: {e}")

def main() -> None:
    """Main execution function."""
    strategy = None
    
    try:
        # Load configuration
        config = load_config()
        
        # Initialize components
        client = KrakenClient()
        indicator = Indicator(client)
        strategy = LimitStrategy(config, client, indicator, test_mode=True)
        
        # Setup shutdown handler
        signal.signal(signal.SIGINT, lambda s, f: handle_shutdown(strategy))
        signal.signal(signal.SIGTERM, lambda s, f: handle_shutdown(strategy))
        
        # Main trading loop
        logger.info("Starting trading bot...")
        while running:
            try:
                strategy.execute()
                time.sleep(config['check_interval'])
            except Exception as e:
                logger.error(f"Error during execution: {e}")
                time.sleep(60)  # Wait before retry
                
        logger.info("Trading bot stopped")
                
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        handle_shutdown(strategy)

if __name__ == "__main__":
    main()