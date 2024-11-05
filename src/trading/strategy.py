import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class LimitStrategy:
    """
    Implements a limit order strategy based on SMA deviations.
    Places buy orders when price deviates below SMA and sell orders at entry SMA.
    """
    
    def __init__(
        self, 
        config: Dict[str, Any],
        kraken_client: Any,
        indicator: Any,
        test_mode: bool = True
    ) -> None:
        """
        Initialize the strategy.

        Args:
            config: Trading configuration parameters
            kraken_client: Instance of KrakenClient for API interactions
            indicator: Instance of Indicator for technical analysis
            test_mode: If True, orders are only validated not placed
        """
        self.config = config
        self.client = kraken_client
        self.indicator = indicator
        self.test_mode = test_mode
        
        # Trading state
        self.active_order: Optional[str] = None
        self.entry_sma: Optional[float] = None
        self.in_position = False
        
        logger.info(f"Strategy initialized in {'test' if test_mode else 'live'} mode")

    def format_price(self, price: float) -> float:
        """Format price to match exchange requirements."""
        return round(price, 1)  # Kraken requires 1 decimal for XBTUSD

    def check_balance_for_order(self) -> bool:
        """Verify sufficient balance for order."""
        try:
            if self.test_mode:
                return True
                
            balance = self.client.get_account_balance()
            required = self.config['volume'] * self.calculate_target_price()
            has_balance = float(balance.get(self.config['base_currency'], 0)) >= required
            
            if not has_balance:
                logger.warning(f"Insufficient balance for order. Required: {required}")
            
            return has_balance
            
        except Exception as e:
            logger.error(f"Error checking balance: {e}")
            return False

    def calculate_target_price(self) -> float:
        """Calculate entry price based on SMA deviation."""
        try:
            # Calculate SMA
            sma = self.indicator.calculate_sma(
                pair=self.config['pair'],
                timeframe=60,  # 1h timeframe
                length=self.config['sma_length']
            )
            
            # Calculate target price with depeg
            target_price = sma * (1 - self.config['depeg_percentage']/100)
            formatted_price = self.format_price(target_price)
            
            logger.info(f"Calculated target price: {formatted_price} (SMA: {sma})")
            return formatted_price
            
        except Exception as e:
            logger.error(f"Error calculating target price: {e}")
            raise

    def execute(self) -> None:
        """Execute one iteration of the trading strategy."""
        try:
            # Entry logic - no position and no active orders
            if not self.in_position and not self.active_order:
                if not self.check_balance_for_order():
                    return
                    
                target_price = self.calculate_target_price()
                
                # Place buy order
                order = self.client.place_limit_order(
                    pair=self.config['pair'],
                    volume=self.config['volume'],
                    price=target_price,
                    side='buy',
                    validate=self.test_mode
                )
                
                if self.test_mode:
                    logger.info(f"TEST MODE: Would place buy order at {target_price}")
                    return
                    
                self.active_order = order['txid'][0]
                self.entry_sma = target_price / (1 - self.config['depeg_percentage']/100)
                logger.info(f"Placed buy order at {target_price}")

            # Order management - only in live mode
            elif self.active_order and not self.test_mode:
                order_details = self.client.get_order_details(self.active_order)
                status = order_details[self.active_order]['status']

                if status == 'closed':  # Order filled
                    if not self.in_position:  # Buy order filled
                        self.in_position = True
                        
                        # Place sell order at entry SMA
                        sell_order = self.client.place_limit_order(
                            pair=self.config['pair'],
                            volume=self.config['volume'],
                            price=self.format_price(self.entry_sma),
                            side='sell',
                            validate=False
                        )
                        self.active_order = sell_order['txid'][0]
                        logger.info(f"Buy order filled, placed sell order at {self.entry_sma}")
                        
                    else:  # Sell order filled
                        self.in_position = False
                        self.active_order = None
                        self.entry_sma = None
                        logger.info("Position closed")

                elif not self.in_position:  # Update buy order if needed
                    new_target = self.calculate_target_price()
                    current_price = float(order_details[self.active_order]['price'])
                    
                    if new_target != current_price:
                        self.client.update_limit_order(
                            pair=self.config['pair'],
                            volume=self.config['volume'],
                            new_price=new_target,
                            order_id=self.active_order,
                            side='buy'
                        )
                        self.active_order = None  # Will be set in next iteration
                        logger.info(f"Updated buy order to new price {new_target}")

        except Exception as e:
            logger.error(f"Error in strategy execution: {e}")