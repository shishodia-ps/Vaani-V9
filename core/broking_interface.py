"""
MT5 Broking Interface
Handles all MetaTrader 5 interactions including connection, data retrieval, and order execution
"""

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    import mock_mt5 as mt5
    MT5_AVAILABLE = False
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass
from enum import Enum

class OrderType(Enum):
    BUY = mt5.ORDER_TYPE_BUY
    SELL = mt5.ORDER_TYPE_SELL
    BUY_LIMIT = mt5.ORDER_TYPE_BUY_LIMIT
    SELL_LIMIT = mt5.ORDER_TYPE_SELL_LIMIT
    BUY_STOP = mt5.ORDER_TYPE_BUY_STOP
    SELL_STOP = mt5.ORDER_TYPE_SELL_STOP

@dataclass
class TradeRequest:
    """Trade request structure"""
    symbol: str
    volume: float
    order_type: OrderType
    price: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    comment: str = "AI Trading Bot"
    magic: int = 12345

@dataclass
class AccountInfo:
    """Account information structure"""
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    profit: float
    currency: str

class MT5Interface:
    """MetaTrader 5 interface for trading operations"""
    
    def __init__(self, login: Optional[str] = None, password: Optional[str] = None, server: Optional[str] = None, path: Optional[str] = None):
        self.login = login
        self.password = password
        self.server = server
        self.path = path
        self.connected = False
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        """Connect to MT5 terminal"""
        try:
            if self.path:
                if not mt5.initialize(path=self.path):
                    self.logger.error(f"MT5 initialize failed: {mt5.last_error()}")
                    return False
            else:
                if not mt5.initialize():
                    self.logger.error(f"MT5 initialize failed: {mt5.last_error()}")
                    return False
            
            if self.login and self.password and self.server:
                if not mt5.login(int(self.login), self.password, self.server):
                    self.logger.error(f"MT5 login failed: {mt5.last_error()}")
                    return False
            
            self.connected = True
            self.logger.info("Successfully connected to MT5")
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting to MT5: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MT5 terminal"""
        mt5.shutdown()
        self.connected = False
        self.logger.info("Disconnected from MT5")
    
    def get_account_info(self) -> Optional[AccountInfo]:
        """Get account information"""
        if not self.connected:
            return None
            
        try:
            account_info = mt5.account_info()
            if account_info is None:
                return None
                
            return AccountInfo(
                balance=account_info.balance,
                equity=account_info.equity,
                margin=account_info.margin,
                free_margin=account_info.margin_free,
                margin_level=account_info.margin_level,
                profit=account_info.profit,
                currency=account_info.currency
            )
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get symbol information"""
        if not self.connected:
            return None
            
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return None
                
            return {
                'symbol': symbol_info.name,
                'bid': symbol_info.bid,
                'ask': symbol_info.ask,
                'spread': symbol_info.spread,
                'point': symbol_info.point,
                'digits': symbol_info.digits,
                'trade_contract_size': symbol_info.trade_contract_size,
                'volume_min': symbol_info.volume_min,
                'volume_max': symbol_info.volume_max,
                'volume_step': symbol_info.volume_step
            }
        except Exception as e:
            self.logger.error(f"Error getting symbol info for {symbol}: {e}")
            return None
    
    def get_rates(self, symbol: str, timeframe: int, count: int = 1000) -> Optional[pd.DataFrame]:
        """Get historical price data"""
        if not self.connected:
            return None
            
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None:
                return None
                
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting rates for {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[Tuple[float, float]]:
        """Get current bid/ask prices"""
        symbol_info = self.get_symbol_info(symbol)
        if symbol_info:
            return symbol_info['bid'], symbol_info['ask']
        return None
    
    def calculate_lot_size(self, symbol: str, risk_percent: float, stop_loss_pips: float, account_balance: float) -> float:
        """Calculate optimal lot size based on risk management"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                return 0.01
            
            risk_amount = account_balance * (risk_percent / 100)
            pip_value = symbol_info['trade_contract_size'] * symbol_info['point']
            
            if symbol_info['symbol'].endswith('JPY'):
                pip_value *= 100
            
            lot_size = risk_amount / (stop_loss_pips * pip_value)
            
            volume_step = symbol_info['volume_step']
            lot_size = round(lot_size / volume_step) * volume_step
            
            lot_size = max(symbol_info['volume_min'], min(lot_size, symbol_info['volume_max']))
            
            return lot_size
            
        except Exception as e:
            self.logger.error(f"Error calculating lot size: {e}")
            return 0.01
    
    def send_order(self, trade_request: TradeRequest) -> Optional[Dict]:
        """Send trading order"""
        if not self.connected:
            return None
            
        try:
            symbol_info = self.get_symbol_info(trade_request.symbol)
            if not symbol_info:
                return None
            
            if trade_request.price is None:
                if trade_request.order_type == OrderType.BUY:
                    trade_request.price = symbol_info['ask']
                else:
                    trade_request.price = symbol_info['bid']
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": trade_request.symbol,
                "volume": trade_request.volume,
                "type": trade_request.order_type.value,
                "price": trade_request.price,
                "sl": trade_request.sl,
                "tp": trade_request.tp,
                "comment": trade_request.comment,
                "magic": trade_request.magic,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Order failed: {result.retcode} - {result.comment}")
                return None
            
            self.logger.info(f"Order successful: {result.order}")
            return {
                'order': result.order,
                'deal': result.deal,
                'volume': result.volume,
                'price': result.price,
                'comment': result.comment
            }
            
        except Exception as e:
            self.logger.error(f"Error sending order: {e}")
            return None
    
    def get_positions(self) -> List[Dict]:
        """Get current open positions"""
        if not self.connected:
            return []
            
        try:
            positions = mt5.positions_get()
            if positions is None:
                return []
            
            return [
                {
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': pos.type,
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'profit': pos.profit,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'comment': pos.comment,
                    'time': datetime.fromtimestamp(pos.time)
                }
                for pos in positions
            ]
            
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []
    
    def close_position(self, ticket: int) -> bool:
        """Close a specific position"""
        if not self.connected:
            return False
            
        try:
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                return False
            
            position = positions[0]
            
            if position.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(position.symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(position.symbol).ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": order_type,
                "position": ticket,
                "price": price,
                "comment": "Close by AI Bot",
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"Position {ticket} closed successfully")
                return True
            else:
                self.logger.error(f"Failed to close position {ticket}: {result.comment}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error closing position {ticket}: {e}")
            return False
    
    def get_history_deals(self, days: int = 30) -> List[Dict]:
        """Get trading history"""
        if not self.connected:
            return []
            
        try:
            from_date = datetime.now() - timedelta(days=days)
            to_date = datetime.now()
            
            deals = mt5.history_deals_get(from_date, to_date)
            if deals is None:
                return []
            
            return [
                {
                    'ticket': deal.ticket,
                    'order': deal.order,
                    'symbol': deal.symbol,
                    'type': deal.type,
                    'volume': deal.volume,
                    'price': deal.price,
                    'profit': deal.profit,
                    'commission': deal.commission,
                    'swap': deal.swap,
                    'time': datetime.fromtimestamp(deal.time),
                    'comment': deal.comment
                }
                for deal in deals
            ]
            
        except Exception as e:
            self.logger.error(f"Error getting history deals: {e}")
            return []
