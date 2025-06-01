"""
Mock MetaTrader5 interface for testing and development
Provides the same API as MT5 but with simulated data
"""

import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import pandas as pd

@dataclass
class MockPosition:
    """Mock MT5 position"""
    ticket: int
    time: int
    time_msc: int
    time_update: int
    time_update_msc: int
    type: int  # 0=buy, 1=sell
    magic: int
    identifier: int
    reason: int
    volume: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    swap: float
    profit: float
    symbol: str
    comment: str
    external_id: str

@dataclass
class MockOrder:
    """Mock MT5 order"""
    ticket: int
    time_setup: int
    time_setup_msc: int
    time_done: int
    time_done_msc: int
    time_expiration: int
    type: int
    type_time: int
    type_filling: int
    state: int
    magic: int
    position_id: int
    position_by_id: int
    reason: int
    volume_initial: float
    volume_current: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    price_stoplimit: float
    symbol: str
    comment: str
    external_id: str

@dataclass
class MockAccountInfo:
    """Mock MT5 account info"""
    login: int = 12345678
    trade_mode: int = 0
    leverage: int = 100
    limit_orders: int = 200
    margin_so_mode: int = 0
    trade_allowed: bool = True
    trade_expert: bool = True
    margin_mode: int = 0
    currency_digits: int = 2
    fifo_close: bool = False
    balance: float = 10000.0
    credit: float = 0.0
    profit: float = 0.0
    equity: float = 10000.0
    margin: float = 0.0
    margin_free: float = 10000.0
    margin_level: float = 0.0
    margin_call: float = 50.0
    margin_stop_out: float = 20.0
    name: str = "Mock Account"
    server: str = "MockServer"
    currency: str = "USD"
    company: str = "Mock Broker"

class MockMT5:
    """Mock MetaTrader5 interface"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialized = False
        self._connected = False
        self._positions = {}
        self._orders = {}
        self._account_info = MockAccountInfo()
        self._symbols = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD"]
        self._current_prices = {
            "EURUSD": 1.0850,
            "GBPUSD": 1.2650,
            "USDJPY": 149.50,
            "USDCHF": 0.8950,
            "AUDUSD": 0.6750
        }
        self._last_error = 0
        
    def initialize(self, path: str = "", login: int = 0, password: str = "", server: str = "") -> bool:
        """Initialize MT5 connection"""
        self.logger.info("Initializing mock MT5 connection")
        self._initialized = True
        self._connected = True
        return True
    
    def shutdown(self) -> None:
        """Shutdown MT5 connection"""
        self.logger.info("Shutting down mock MT5 connection")
        self._initialized = False
        self._connected = False
    
    def login(self, login: int, password: str = "", server: str = "") -> bool:
        """Login to MT5 account"""
        self.logger.info(f"Mock login to account {login}")
        self._account_info.login = login
        return True
    
    def account_info(self) -> Optional[MockAccountInfo]:
        """Get account information"""
        if not self._connected:
            return None
        
        total_profit = sum(pos.profit for pos in self._positions.values())
        self._account_info.profit = total_profit
        self._account_info.equity = self._account_info.balance + total_profit
        self._account_info.margin_free = self._account_info.equity - self._account_info.margin
        
        if self._account_info.margin > 0:
            self._account_info.margin_level = (self._account_info.equity / self._account_info.margin) * 100
        else:
            self._account_info.margin_level = 0.0
            
        return self._account_info
    
    def positions_get(self, symbol: Optional[str] = None, group: Optional[str] = None, ticket: Optional[int] = None) -> Tuple[MockPosition, ...]:
        """Get open positions"""
        if not self._connected:
            return tuple()
        
        positions = list(self._positions.values())
        
        if symbol:
            positions = [pos for pos in positions if pos.symbol == symbol]
        if ticket:
            positions = [pos for pos in positions if pos.ticket == ticket]
            
        for pos in positions:
            current_price = self._get_current_price(pos.symbol)
            pos.price_current = current_price
            
            if pos.type == 0:  # Buy
                pos.profit = (current_price - pos.price_open) * pos.volume * 100000
            else:  # Sell
                pos.profit = (pos.price_open - current_price) * pos.volume * 100000
                
        return tuple(positions)
    
    def orders_get(self, symbol: Optional[str] = None, group: Optional[str] = None, ticket: Optional[int] = None) -> Tuple[MockOrder, ...]:
        """Get pending orders"""
        if not self._connected:
            return tuple()
        
        orders = list(self._orders.values())
        
        if symbol:
            orders = [order for order in orders if order.symbol == symbol]
        if ticket:
            orders = [order for order in orders if order.ticket == ticket]
            
        return tuple(orders)
    
    def order_send(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send trading order"""
        if not self._connected:
            return {"retcode": 10004, "comment": "Not connected"}
        
        try:
            action = request.get("action")
            symbol = request.get("symbol", "EURUSD")
            volume = request.get("volume", 0.01)
            order_type = request.get("type", 0)
            price = request.get("price", self._get_current_price(symbol))
            sl = request.get("sl", 0.0)
            tp = request.get("tp", 0.0)
            comment = request.get("comment", "")
            magic = request.get("magic", 0)
            
            ticket = random.randint(100000, 999999)
            current_time = int(time.time())
            
            if action == 1:  # ORDER_TYPE_BUY or ORDER_TYPE_SELL
                position = MockPosition(
                    ticket=ticket,
                    time=current_time,
                    time_msc=current_time * 1000,
                    time_update=current_time,
                    time_update_msc=current_time * 1000,
                    type=order_type,
                    magic=magic,
                    identifier=ticket,
                    reason=0,
                    volume=volume,
                    price_open=price,
                    sl=sl,
                    tp=tp,
                    price_current=price,
                    swap=0.0,
                    profit=0.0,
                    symbol=symbol,
                    comment=comment,
                    external_id=""
                )
                
                self._positions[ticket] = position
                
                margin_required = volume * 100000 / self._account_info.leverage
                self._account_info.margin += margin_required
                
                return {
                    "retcode": 10009,  # TRADE_RETCODE_DONE
                    "deal": ticket,
                    "order": ticket,
                    "volume": volume,
                    "price": price,
                    "bid": price - 0.0001,
                    "ask": price + 0.0001,
                    "comment": "Mock order executed",
                    "request_id": 1,
                    "retcode_external": 0
                }
            
            else:
                order = MockOrder(
                    ticket=ticket,
                    time_setup=current_time,
                    time_setup_msc=current_time * 1000,
                    time_done=0,
                    time_done_msc=0,
                    time_expiration=0,
                    type=order_type,
                    type_time=0,
                    type_filling=0,
                    state=1,  # ORDER_STATE_PLACED
                    magic=magic,
                    position_id=0,
                    position_by_id=0,
                    reason=0,
                    volume_initial=volume,
                    volume_current=volume,
                    price_open=price,
                    sl=sl,
                    tp=tp,
                    price_current=self._get_current_price(symbol),
                    price_stoplimit=0.0,
                    symbol=symbol,
                    comment=comment,
                    external_id=""
                )
                
                self._orders[ticket] = order
                
                return {
                    "retcode": 10009,
                    "order": ticket,
                    "volume": volume,
                    "price": price,
                    "comment": "Mock pending order placed"
                }
                
        except Exception as e:
            self.logger.error(f"Error in mock order_send: {e}")
            return {"retcode": 10013, "comment": f"Error: {e}"}
    
    def order_close(self, ticket: int, volume: Optional[float] = None) -> Dict[str, Any]:
        """Close position"""
        if not self._connected:
            return {"retcode": 10004, "comment": "Not connected"}
        
        if ticket not in self._positions:
            return {"retcode": 10013, "comment": "Position not found"}
        
        position = self._positions[ticket]
        close_volume = volume or position.volume
        
        if close_volume >= position.volume:
            margin_released = position.volume * 100000 / self._account_info.leverage
            self._account_info.margin -= margin_released
            self._account_info.balance += position.profit
            del self._positions[ticket]
        else:
            position.volume -= close_volume
            margin_released = close_volume * 100000 / self._account_info.leverage
            self._account_info.margin -= margin_released
            
            profit_per_lot = position.profit / (position.volume + close_volume)
            closed_profit = profit_per_lot * close_volume
            self._account_info.balance += closed_profit
            position.profit -= closed_profit
        
        return {
            "retcode": 10009,
            "deal": ticket,
            "volume": close_volume,
            "comment": "Mock position closed"
        }
    
    def copy_rates_from_pos(self, symbol: str, timeframe: int, start_pos: int, count: int) -> Optional[pd.DataFrame]:
        """Get historical rates"""
        if not self._connected:
            return None
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=count)
        
        dates = pd.date_range(start=start_time, end=end_time, freq='H')[:count]
        base_price = self._current_prices.get(symbol, 1.0000)
        
        data = []
        for i, date in enumerate(dates):
            open_price = base_price + random.uniform(-0.01, 0.01)
            high_price = open_price + random.uniform(0, 0.005)
            low_price = open_price - random.uniform(0, 0.005)
            close_price = open_price + random.uniform(-0.003, 0.003)
            volume = random.randint(100, 1000)
            
            data.append({
                'time': int(date.timestamp()),
                'open': round(open_price, 5),
                'high': round(high_price, 5),
                'low': round(low_price, 5),
                'close': round(close_price, 5),
                'tick_volume': volume,
                'spread': 2,
                'real_volume': volume
            })
            
            base_price = close_price  # Use close as next open
        
        df = pd.DataFrame(data)
        return df
    
    def symbol_info_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current tick information"""
        if not self._connected:
            return None
        
        price = self._get_current_price(symbol)
        spread = 0.0002  # 2 pips
        
        return {
            'time': int(time.time()),
            'bid': round(price - spread/2, 5),
            'ask': round(price + spread/2, 5),
            'last': round(price, 5),
            'volume': random.randint(1, 10),
            'time_msc': int(time.time() * 1000),
            'flags': 6,
            'volume_real': random.uniform(0.1, 5.0)
        }
    
    def symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information"""
        if not self._connected:
            return None
        
        return {
            'custom': False,
            'chart_mode': 0,
            'select': True,
            'visible': True,
            'session_deals': 1000,
            'session_buy_orders': 500,
            'session_sell_orders': 500,
            'volume': 1000,
            'volumehigh': 2000,
            'volumelow': 100,
            'time': int(time.time()),
            'digits': 5,
            'spread': 2,
            'spread_float': True,
            'ticks_bookdepth': 10,
            'trade_calc_mode': 0,
            'trade_mode': 4,
            'start_time': 0,
            'expiration_time': 0,
            'trade_stops_level': 0,
            'trade_freeze_level': 0,
            'trade_exemode': 2,
            'swap_mode': 1,
            'swap_rollover3days': 3,
            'margin_hedged_use_leg': False,
            'expiration_mode': 7,
            'filling_mode': 1,
            'order_mode': 127,
            'order_gtc_mode': 0,
            'option_mode': 0,
            'option_right': 0,
            'bid': self._get_current_price(symbol) - 0.0001,
            'bidhigh': self._get_current_price(symbol),
            'bidlow': self._get_current_price(symbol) - 0.002,
            'ask': self._get_current_price(symbol) + 0.0001,
            'askhigh': self._get_current_price(symbol) + 0.001,
            'asklow': self._get_current_price(symbol) - 0.001,
            'last': self._get_current_price(symbol),
            'lasthigh': self._get_current_price(symbol) + 0.001,
            'lastlow': self._get_current_price(symbol) - 0.001,
            'volume_real': 1000.0,
            'volumehigh_real': 2000.0,
            'volumelow_real': 100.0,
            'option_strike': 0.0,
            'point': 0.00001,
            'trade_tick_value': 1.0,
            'trade_tick_value_profit': 1.0,
            'trade_tick_value_loss': 1.0,
            'trade_tick_size': 0.00001,
            'trade_contract_size': 100000.0,
            'trade_accrued_interest': 0.0,
            'trade_face_value': 0.0,
            'trade_liquidity_rate': 0.0,
            'volume_min': 0.01,
            'volume_max': 500.0,
            'volume_step': 0.01,
            'volume_limit': 0.0,
            'swap_long': -0.5,
            'swap_short': -0.5,
            'margin_initial': 0.0,
            'margin_maintenance': 0.0,
            'session_volume': 1000.0,
            'session_turnover': 100000.0,
            'session_interest': 0.0,
            'session_buy_orders_volume': 500.0,
            'session_sell_orders_volume': 500.0,
            'session_open': self._get_current_price(symbol),
            'session_close': self._get_current_price(symbol),
            'session_aw': self._get_current_price(symbol),
            'session_price_settlement': self._get_current_price(symbol),
            'session_price_limit_min': 0.0,
            'session_price_limit_max': 0.0,
            'margin_hedged': 50000.0,
            'price_change': random.uniform(-0.001, 0.001),
            'price_volatility': random.uniform(0.1, 0.5),
            'price_theoretical': self._get_current_price(symbol),
            'price_greeks_delta': 0.0,
            'price_greeks_theta': 0.0,
            'price_greeks_gamma': 0.0,
            'price_greeks_vega': 0.0,
            'price_greeks_rho': 0.0,
            'price_greeks_omega': 0.0,
            'price_sensitivity': 0.0,
            'basis': '',
            'category': '',
            'currency_base': symbol[:3],
            'currency_profit': symbol[3:],
            'currency_margin': symbol[3:],
            'bank': '',
            'description': f'Mock {symbol}',
            'exchange': 'MockExchange',
            'formula': '',
            'isin': '',
            'name': symbol,
            'page': '',
            'path': symbol
        }
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current price with some random movement"""
        base_price = self._current_prices.get(symbol, 1.0000)
        
        movement = random.uniform(-0.0005, 0.0005)
        new_price = base_price + movement
        
        self._current_prices[symbol] = new_price
        
        return round(new_price, 5)
    
    def last_error(self) -> int:
        """Get last error code"""
        return self._last_error
    
    def version(self) -> Tuple[int, int, str]:
        """Get MT5 version"""
        return (5, 0, "Mock MT5 Interface")

mock_mt5 = MockMT5()

def initialize(path: str = "", login: int = 0, password: str = "", server: str = "") -> bool:
    return mock_mt5.initialize(path, login, password, server)

def shutdown() -> None:
    return mock_mt5.shutdown()

def login(login: int, password: str = "", server: str = "") -> bool:
    return mock_mt5.login(login, password, server)

def account_info():
    return mock_mt5.account_info()

def positions_get(symbol: Optional[str] = None, group: Optional[str] = None, ticket: Optional[int] = None):
    return mock_mt5.positions_get(symbol, group, ticket)

def orders_get(symbol: Optional[str] = None, group: Optional[str] = None, ticket: Optional[int] = None):
    return mock_mt5.orders_get(symbol, group, ticket)

def order_send(request: Dict[str, Any]):
    return mock_mt5.order_send(request)

def copy_rates_from_pos(symbol: str, timeframe: int, start_pos: int, count: int):
    return mock_mt5.copy_rates_from_pos(symbol, timeframe, start_pos, count)

def symbol_info_tick(symbol: str):
    return mock_mt5.symbol_info_tick(symbol)

def symbol_info(symbol: str):
    return mock_mt5.symbol_info(symbol)

def last_error() -> int:
    return mock_mt5.last_error()

def version():
    return mock_mt5.version()

TIMEFRAME_M1 = 1
TIMEFRAME_M5 = 5
TIMEFRAME_M15 = 15
TIMEFRAME_M30 = 30
TIMEFRAME_H1 = 16385
TIMEFRAME_H4 = 16388
TIMEFRAME_D1 = 16408

ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1
ORDER_TYPE_BUY_LIMIT = 2
ORDER_TYPE_SELL_LIMIT = 3
ORDER_TYPE_BUY_STOP = 4
ORDER_TYPE_SELL_STOP = 5

TRADE_ACTION_DEAL = 1
TRADE_ACTION_PENDING = 5
TRADE_ACTION_SLTP = 6
TRADE_ACTION_MODIFY = 7
TRADE_ACTION_REMOVE = 8
TRADE_ACTION_CLOSE_BY = 10
