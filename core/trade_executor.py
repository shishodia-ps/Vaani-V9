"""
Trade execution engine with risk management and order management
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import threading
from queue import Queue, Empty

from .broking_interface import MT5Interface, TradeRequest, OrderType
from .config_loader import config

class TradeStatus(Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"

class TradeDirection(Enum):
    BUY = "buy"
    SELL = "sell"

@dataclass
class TradeSignal:
    """Trade signal from strategy"""
    symbol: str
    direction: TradeDirection
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_percent: float = 2.0
    strategy_name: str = "unknown"
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutedTrade:
    """Executed trade record"""
    signal: TradeSignal
    ticket: Optional[int] = None
    executed_price: Optional[float] = None
    volume: float = 0.0
    status: TradeStatus = TradeStatus.PENDING
    execution_time: Optional[datetime] = None
    error_message: Optional[str] = None
    slippage: float = 0.0
    commission: float = 0.0

class TradeExecutor:
    """Handles trade execution with risk management"""
    
    def __init__(self, mt5_interface: MT5Interface):
        self.mt5_interface = mt5_interface
        self.logger = logging.getLogger(__name__)
        self.trade_queue = Queue()
        self.executed_trades: List[ExecutedTrade] = []
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()
        self.running = False
        self.executor_thread = None
        self.max_slippage_pips = 3.0
        self.max_spread_pips = 5.0
        
    def start_executor(self):
        """Start the trade execution thread"""
        if self.running:
            return
        
        self.running = True
        self.executor_thread = threading.Thread(target=self._execution_loop)
        self.executor_thread.daemon = True
        self.executor_thread.start()
        self.logger.info("Trade executor started")
    
    def stop_executor(self):
        """Stop the trade execution thread"""
        self.running = False
        if self.executor_thread:
            self.executor_thread.join(timeout=5)
        self.logger.info("Trade executor stopped")
    
    def submit_trade_signal(self, signal: TradeSignal) -> bool:
        """Submit a trade signal for execution"""
        try:
            if not self._validate_signal(signal):
                return False
            
            if not self._check_daily_limits():
                self.logger.warning("Daily trade limit reached")
                return False
            
            self.trade_queue.put(signal)
            self.logger.info(f"Trade signal submitted: {signal.symbol} {signal.direction.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error submitting trade signal: {e}")
            return False
    
    def _validate_signal(self, signal: TradeSignal) -> bool:
        """Validate trade signal"""
        if not signal.symbol:
            self.logger.error("Invalid signal: missing symbol")
            return False
        
        if signal.risk_percent <= 0 or signal.risk_percent > 10:
            self.logger.error(f"Invalid risk percent: {signal.risk_percent}")
            return False
        
        if signal.confidence < 0 or signal.confidence > 1:
            self.logger.error(f"Invalid confidence: {signal.confidence}")
            return False
        
        return True
    
    def _check_daily_limits(self) -> bool:
        """Check if daily trading limits are exceeded"""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_trades = 0
            self.daily_pnl = 0.0
            self.last_reset_date = current_date
        
        if self.daily_trades >= config.trading.max_daily_trades:
            return False
        
        account_info = self.mt5_interface.get_account_info()
        if account_info:
            drawdown_percent = ((account_info.balance - account_info.equity) / account_info.balance) * 100
            if drawdown_percent > config.trading.max_drawdown_percent:
                self.logger.warning(f"Drawdown limit exceeded: {drawdown_percent:.2f}%")
                return False
        
        return True
    
    def _execution_loop(self):
        """Main trade execution loop"""
        while self.running:
            try:
                signal = self.trade_queue.get(timeout=1)
                
                executed_trade = self._execute_signal(signal)
                self.executed_trades.append(executed_trade)
                
                if executed_trade.status == TradeStatus.EXECUTED:
                    self.daily_trades += 1
                
                self.trade_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in execution loop: {e}")
                time.sleep(1)
    
    def _execute_signal(self, signal: TradeSignal) -> ExecutedTrade:
        """Execute a single trade signal"""
        executed_trade = ExecutedTrade(signal=signal)
        
        try:
            if not self._check_market_conditions(signal.symbol):
                executed_trade.status = TradeStatus.FAILED
                executed_trade.error_message = "Poor market conditions"
                return executed_trade
            
            prices = self.mt5_interface.get_current_price(signal.symbol)
            if not prices:
                executed_trade.status = TradeStatus.FAILED
                executed_trade.error_message = "Unable to get current price"
                return executed_trade
            
            bid, ask = prices
            spread_pips = self._calculate_spread_pips(signal.symbol, bid, ask)
            
            if spread_pips > self.max_spread_pips:
                executed_trade.status = TradeStatus.FAILED
                executed_trade.error_message = f"Spread too wide: {spread_pips} pips"
                return executed_trade
            
            account_info = self.mt5_interface.get_account_info()
            if not account_info:
                executed_trade.status = TradeStatus.FAILED
                executed_trade.error_message = "Unable to get account info"
                return executed_trade
            
            if signal.stop_loss:
                if signal.direction == TradeDirection.BUY:
                    entry_price = signal.entry_price or ask
                    sl_pips = self._calculate_pips(signal.symbol, entry_price - signal.stop_loss)
                else:
                    entry_price = signal.entry_price or bid
                    sl_pips = self._calculate_pips(signal.symbol, signal.stop_loss - entry_price)
            else:
                sl_pips = 20  # Default 20 pips
            
            lot_size = self.mt5_interface.calculate_lot_size(
                signal.symbol, 
                signal.risk_percent, 
                sl_pips, 
                account_info.balance
            )
            
            order_type = OrderType.BUY if signal.direction == TradeDirection.BUY else OrderType.SELL
            trade_request = TradeRequest(
                symbol=signal.symbol,
                volume=lot_size,
                order_type=order_type,
                price=signal.entry_price,
                sl=signal.stop_loss,
                tp=signal.take_profit,
                comment=f"AI Bot - {signal.strategy_name}",
                magic=12345
            )
            
            result = self.mt5_interface.send_order(trade_request)
            
            if result:
                executed_trade.ticket = result.get('order')
                executed_trade.executed_price = result.get('price')
                executed_trade.volume = lot_size
                executed_trade.status = TradeStatus.EXECUTED
                executed_trade.execution_time = datetime.now()
                
                expected_price = ask if signal.direction == TradeDirection.BUY else bid
                if executed_trade.executed_price:
                    slippage_pips = self._calculate_pips(
                        signal.symbol, 
                        abs(executed_trade.executed_price - expected_price)
                    )
                    executed_trade.slippage = slippage_pips
                
                self.logger.info(f"Trade executed: {signal.symbol} {signal.direction.value} "
                               f"Volume: {lot_size} Price: {executed_trade.executed_price}")
            else:
                executed_trade.status = TradeStatus.FAILED
                executed_trade.error_message = "Order execution failed"
                
        except Exception as e:
            executed_trade.status = TradeStatus.FAILED
            executed_trade.error_message = str(e)
            self.logger.error(f"Error executing trade: {e}")
        
        return executed_trade
    
    def _check_market_conditions(self, symbol: str) -> bool:
        """Check if market conditions are suitable for trading"""
        try:
            now = datetime.now()
            if now.weekday() >= 5:  # Weekend
                return False
            
            symbol_info = self.mt5_interface.get_symbol_info(symbol)
            if not symbol_info:
                return False
            
            spread_pips = self._calculate_spread_pips(symbol, symbol_info['bid'], symbol_info['ask'])
            if spread_pips > self.max_spread_pips:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking market conditions: {e}")
            return False
    
    def _calculate_pips(self, symbol: str, price_diff: float) -> float:
        """Calculate pip value for price difference"""
        symbol_info = self.mt5_interface.get_symbol_info(symbol)
        if not symbol_info:
            return 0.0
        
        if symbol.endswith('JPY'):
            return price_diff * 100  # JPY pairs have different pip calculation
        else:
            return price_diff * 10000  # Standard pip calculation
    
    def _calculate_spread_pips(self, symbol: str, bid: float, ask: float) -> float:
        """Calculate spread in pips"""
        return self._calculate_pips(symbol, ask - bid)
    
    def get_trade_statistics(self) -> Dict[str, Any]:
        """Get trading statistics"""
        if not self.executed_trades:
            return {}
        
        executed_only = [t for t in self.executed_trades if t.status == TradeStatus.EXECUTED]
        
        if not executed_only:
            return {'total_trades': 0}
        
        total_trades = len(executed_only)
        avg_slippage = sum(t.slippage for t in executed_only) / total_trades
        
        positions = self.mt5_interface.get_positions()
        current_pnl = sum(pos['profit'] for pos in positions)
        
        return {
            'total_trades': total_trades,
            'daily_trades': self.daily_trades,
            'avg_slippage_pips': avg_slippage,
            'current_pnl': current_pnl,
            'open_positions': len(positions),
            'success_rate': self._calculate_success_rate(),
            'last_trade_time': executed_only[-1].execution_time if executed_only else None
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate trade success rate based on closed positions"""
        return 0.0
    
    def get_open_positions(self) -> List[Dict]:
        """Get current open positions"""
        return self.mt5_interface.get_positions()
    
    def close_position(self, ticket: int) -> bool:
        """Close a specific position"""
        return self.mt5_interface.close_position(ticket)
    
    def close_all_positions(self) -> int:
        """Close all open positions"""
        positions = self.get_open_positions()
        closed_count = 0
        
        for position in positions:
            if self.close_position(position['ticket']):
                closed_count += 1
        
        return closed_count
    
    def emergency_stop(self):
        """Emergency stop - close all positions and stop trading"""
        self.logger.warning("Emergency stop activated")
        
        closed_count = self.close_all_positions()
        self.logger.info(f"Closed {closed_count} positions")
        
        self.stop_executor()
        
        while not self.trade_queue.empty():
            try:
                self.trade_queue.get_nowait()
                self.trade_queue.task_done()
            except Empty:
                break
