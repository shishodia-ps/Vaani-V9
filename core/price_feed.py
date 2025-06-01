"""
Real-time price feed manager
Handles live price data streaming and historical data management
"""

import asyncio
import websocket
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
import pandas as pd
import numpy as np
import logging
from dataclasses import dataclass
from queue import Queue
import yfinance as yf

@dataclass
class PriceTick:
    """Price tick data structure"""
    symbol: str
    bid: float
    ask: float
    timestamp: datetime
    spread: float = 0.0
    volume: int = 0

@dataclass
class OHLCV:
    """OHLCV candle data structure"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    timeframe: str

class PriceFeedManager:
    """Manages real-time and historical price data"""
    
    def __init__(self, mt5_interface=None):
        self.mt5_interface = mt5_interface
        self.logger = logging.getLogger(__name__)
        self.subscribers: Dict[str, List[Callable]] = {}
        self.price_cache: Dict[str, PriceTick] = {}
        self.historical_cache: Dict[str, pd.DataFrame] = {}
        self.running = False
        self.update_thread = None
        self.price_queue = Queue()
        
    def subscribe_to_symbol(self, symbol: str, callback: Callable[[PriceTick], None]):
        """Subscribe to price updates for a symbol"""
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        self.subscribers[symbol].append(callback)
        self.logger.info(f"Subscribed to {symbol} price updates")
    
    def unsubscribe_from_symbol(self, symbol: str, callback: Callable[[PriceTick], None]):
        """Unsubscribe from price updates"""
        if symbol in self.subscribers and callback in self.subscribers[symbol]:
            self.subscribers[symbol].remove(callback)
            if not self.subscribers[symbol]:
                del self.subscribers[symbol]
    
    def get_current_price(self, symbol: str) -> Optional[PriceTick]:
        """Get current cached price for symbol"""
        if symbol in self.price_cache:
            return self.price_cache[symbol]
        
        if self.mt5_interface and self.mt5_interface.connected:
            prices = self.mt5_interface.get_current_price(symbol)
            if prices:
                bid, ask = prices
                tick = PriceTick(
                    symbol=symbol,
                    bid=bid,
                    ask=ask,
                    timestamp=datetime.now(),
                    spread=ask - bid
                )
                self.price_cache[symbol] = tick
                return tick
        
        return None
    
    def get_historical_data(self, symbol: str, timeframe: str, periods: int = 1000) -> Optional[pd.DataFrame]:
        """Get historical price data"""
        cache_key = f"{symbol}_{timeframe}_{periods}"
        
        if cache_key in self.historical_cache:
            cached_data = self.historical_cache[cache_key]
            if (datetime.now() - cached_data.index[-1]).total_seconds() < 60:
                return cached_data
        
        if self.mt5_interface and self.mt5_interface.connected:
            timeframe_map = {
                'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30,
                'H1': 16385, 'H4': 16388, 'D1': 16408
            }
            
            if timeframe in timeframe_map:
                df = self.mt5_interface.get_rates(symbol, timeframe_map[timeframe], periods)
                if df is not None:
                    self.historical_cache[cache_key] = df
                    return df
        
        try:
            if symbol == 'EURUSD':
                yf_symbol = 'EURUSD=X'
            elif symbol == 'GBPUSD':
                yf_symbol = 'GBPUSD=X'
            elif symbol == 'USDJPY':
                yf_symbol = 'USDJPY=X'
            else:
                yf_symbol = f"{symbol}=X"
            
            interval_map = {
                'M1': '1m', 'M5': '5m', 'M15': '15m', 'M30': '30m',
                'H1': '1h', 'H4': '4h', 'D1': '1d'
            }
            
            if timeframe in interval_map:
                ticker = yf.Ticker(yf_symbol)
                df = ticker.history(period="1mo", interval=interval_map[timeframe])
                
                if not df.empty:
                    df.columns = [col.lower() for col in df.columns]
                    df['tick_volume'] = df.get('volume', 0)
                    df['real_volume'] = df.get('volume', 0)
                    
                    self.historical_cache[cache_key] = df
                    return df
                    
        except Exception as e:
            self.logger.error(f"Error getting historical data from Yahoo Finance: {e}")
        
        return None
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate common technical indicators"""
        if df is None or df.empty:
            return df
        
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.Series(np.maximum(high_low, np.maximum(high_close, low_close)), index=df.index)
        df['atr'] = true_range.rolling(window=14).mean()
        
        lowest_low = df['low'].rolling(window=14).min()
        highest_high = df['high'].rolling(window=14).max()
        df['stoch_k'] = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
        df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
        
        return df
    
    def start_price_feed(self):
        """Start the price feed update loop"""
        if self.running:
            return
        
        self.running = True
        self.update_thread = threading.Thread(target=self._price_update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        self.logger.info("Price feed started")
    
    def stop_price_feed(self):
        """Stop the price feed"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        self.logger.info("Price feed stopped")
    
    def _price_update_loop(self):
        """Main price update loop"""
        while self.running:
            try:
                for symbol in self.subscribers.keys():
                    tick = self.get_current_price(symbol)
                    if tick:
                        self.price_cache[symbol] = tick
                        for callback in self.subscribers[symbol]:
                            try:
                                callback(tick)
                            except Exception as e:
                                self.logger.error(f"Error in price callback for {symbol}: {e}")
                
                time.sleep(1)  # Update every second
                
            except Exception as e:
                self.logger.error(f"Error in price update loop: {e}")
                time.sleep(5)  # Wait longer on error
    
    def get_market_hours(self, symbol: str) -> Dict[str, Any]:
        """Get market hours information for symbol"""
        if any(pair in symbol.upper() for pair in ['EUR', 'USD', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD']):
            now = datetime.now()
            if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return {
                    'is_open': False,
                    'next_open': self._next_monday_open(),
                    'session': 'closed'
                }
            
            return {
                'is_open': True,
                'next_close': self._next_friday_close(),
                'session': self._get_forex_session(now)
            }
        
        return {'is_open': True, 'session': 'unknown'}
    
    def _next_monday_open(self) -> datetime:
        """Get next Monday market open time"""
        now = datetime.now()
        days_ahead = 7 - now.weekday()  # Monday is 0
        if days_ahead <= 0:
            days_ahead += 7
        return (now + timedelta(days=days_ahead)).replace(hour=22, minute=0, second=0, microsecond=0)
    
    def _next_friday_close(self) -> datetime:
        """Get next Friday market close time"""
        now = datetime.now()
        days_ahead = 4 - now.weekday()  # Friday is 4
        if days_ahead < 0:
            days_ahead += 7
        return (now + timedelta(days=days_ahead)).replace(hour=22, minute=0, second=0, microsecond=0)
    
    def _get_forex_session(self, dt: datetime) -> str:
        """Determine current forex trading session"""
        hour = dt.hour
        
        if 22 <= hour or hour < 8:
            return 'Sydney/Tokyo'
        elif 8 <= hour < 16:
            return 'London'
        elif 16 <= hour < 22:
            return 'New York'
        else:
            return 'overlap'
    
    def get_volatility_metrics(self, symbol: str, periods: int = 100) -> Dict[str, float]:
        """Calculate volatility metrics for symbol"""
        df = self.get_historical_data(symbol, 'H1', periods)
        if df is None or df.empty:
            return {}
        
        returns = df['close'].pct_change().dropna()
        
        return {
            'volatility_1h': returns.std() * np.sqrt(24),  # Annualized hourly volatility
            'volatility_daily': returns.std() * np.sqrt(24 * 365),  # Annualized daily volatility
            'avg_true_range': df['atr'].iloc[-1] if 'atr' in df.columns else 0,
            'price_range_pct': ((df['high'].max() - df['low'].min()) / df['close'].iloc[-1]) * 100,
            'recent_volatility': returns.tail(24).std() * np.sqrt(24)  # Last 24 hours
        }
