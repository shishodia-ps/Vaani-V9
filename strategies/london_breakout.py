"""
London Breakout Strategy
Trades breakouts during London session opening hours
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, time

class LondonBreakoutStrategy:
    """London session breakout trading strategy"""
    
    def __init__(self, 
                 london_start: time = time(8, 0),  # 8:00 GMT
                 london_end: time = time(17, 0),   # 17:00 GMT
                 breakout_period: int = 30,        # Minutes to establish range
                 min_range_pips: float = 15.0,
                 max_range_pips: float = 80.0,
                 stop_loss_pips: float = 20.0,
                 take_profit_ratio: float = 2.0):
        
        self.london_start = london_start
        self.london_end = london_end
        self.breakout_period = breakout_period
        self.min_range_pips = min_range_pips
        self.max_range_pips = max_range_pips
        self.stop_loss_pips = stop_loss_pips
        self.take_profit_ratio = take_profit_ratio
        
        self.logger = logging.getLogger(__name__)
        self.session_high = None
        self.session_low = None
        self.range_established = False
        
    def analyze(self, data: pd.DataFrame, symbol: str = "EURUSD") -> Dict[str, Any]:
        """Analyze market for London breakout opportunities"""
        try:
            if len(data) < 50:
                return self._no_signal_result("Insufficient data")
            
            current_time = datetime.now().time()
            current_price = data['close'].iloc[-1]
            
            session_info = self._check_london_session(current_time)
            
            if not session_info['in_session']:
                return self._no_signal_result("Outside London session")
            
            self._update_session_range(data, session_info)
            
            signal = self._detect_breakout(data, current_price)
            
            market_analysis = self._analyze_market_conditions(data)
            
            return {
                'signal': signal['type'],
                'confidence': signal['confidence'],
                'entry_price': current_price,
                'session_high': self.session_high,
                'session_low': self.session_low,
                'range_pips': signal.get('range_pips', 0),
                'breakout_strength': signal.get('strength', 0),
                'analysis': {
                    'strategy': 'London Breakout',
                    'session_status': session_info,
                    'range_established': self.range_established,
                    'market_conditions': market_analysis,
                    'breakout_direction': signal.get('direction', 'NONE')
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in London breakout analysis: {e}")
            return self._no_signal_result(f"Analysis error: {e}")
    
    def _check_london_session(self, current_time: time) -> Dict[str, Any]:
        """Check if current time is within London session"""
        
        in_session = self.london_start <= current_time <= self.london_end
        
        if in_session:
            session_start_minutes = self.london_start.hour * 60 + self.london_start.minute
            current_minutes = current_time.hour * 60 + current_time.minute
            minutes_since_start = current_minutes - session_start_minutes
        else:
            minutes_since_start = 0
        
        return {
            'in_session': in_session,
            'minutes_since_start': minutes_since_start,
            'range_period_active': in_session and minutes_since_start <= self.breakout_period,
            'breakout_period_active': in_session and minutes_since_start > self.breakout_period
        }
    
    def _update_session_range(self, data: pd.DataFrame, session_info: Dict[str, Any]):
        """Update session high/low range"""
        
        if session_info['range_period_active']:
            recent_data = data.tail(self.breakout_period)
            
            if self.session_high is None or self.session_low is None:
                self.session_high = recent_data['high'].max()
                self.session_low = recent_data['low'].min()
            else:
                self.session_high = max(self.session_high, recent_data['high'].max())
                self.session_low = min(self.session_low, recent_data['low'].min())
            
            range_pips = (self.session_high - self.session_low) * 10000
            if range_pips >= self.min_range_pips:
                self.range_established = True
        
        elif not session_info['in_session']:
            self.session_high = None
            self.session_low = None
            self.range_established = False
    
    def _detect_breakout(self, data: pd.DataFrame, current_price: float) -> Dict[str, Any]:
        """Detect breakout signals"""
        
        if not self.range_established or self.session_high is None or self.session_low is None:
            return {'type': 'HOLD', 'confidence': 0.0}
        
        range_pips = (self.session_high - self.session_low) * 10000
        
        if range_pips > self.max_range_pips:
            return {'type': 'HOLD', 'confidence': 0.0, 'reason': 'Range too wide'}
        
        pip_value = 0.0001  # For EURUSD
        breakout_buffer = 2 * pip_value  # 2 pip buffer
        
        upper_breakout = self.session_high + breakout_buffer
        lower_breakout = self.session_low - breakout_buffer
        
        if current_price > upper_breakout:
            strength = self._calculate_breakout_strength(data, 'bullish')
            confidence = min(0.8, 0.5 + (strength * 0.3))
            
            return {
                'type': 'BUY',
                'direction': 'BULLISH',
                'confidence': confidence,
                'strength': strength,
                'range_pips': range_pips,
                'breakout_level': upper_breakout
            }
        
        elif current_price < lower_breakout:
            strength = self._calculate_breakout_strength(data, 'bearish')
            confidence = min(0.8, 0.5 + (strength * 0.3))
            
            return {
                'type': 'SELL',
                'direction': 'BEARISH',
                'confidence': confidence,
                'strength': strength,
                'range_pips': range_pips,
                'breakout_level': lower_breakout
            }
        
        return {'type': 'HOLD', 'confidence': 0.0}
    
    def _calculate_breakout_strength(self, data: pd.DataFrame, direction: str) -> float:
        """Calculate strength of breakout"""
        
        recent_data = data.tail(10)
        avg_range = (recent_data['high'] - recent_data['low']).mean()
        current_range = data['high'].iloc[-1] - data['low'].iloc[-1]
        
        volume_strength = min(2.0, current_range / avg_range) if avg_range > 0 else 1.0
        
        price_change = data['close'].iloc[-1] - data['close'].iloc[-5]
        momentum_strength = abs(price_change) * 10000  # Convert to pips
        momentum_strength = min(1.0, momentum_strength / 10.0)  # Normalize
        
        overall_strength = (volume_strength + momentum_strength) / 2
        return min(1.0, overall_strength)
    
    def _analyze_market_conditions(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze overall market conditions"""
        
        returns = data['close'].pct_change().dropna()
        volatility = returns.tail(20).std()
        
        sma_20 = data['close'].rolling(20).mean()
        sma_50 = data['close'].rolling(50).mean() if len(data) >= 50 else sma_20
        
        current_price = data['close'].iloc[-1]
        trend_strength = abs(current_price - sma_20.iloc[-1]) / sma_20.iloc[-1]
        
        if current_price > sma_20.iloc[-1] > sma_50.iloc[-1]:
            sentiment = 'BULLISH'
        elif current_price < sma_20.iloc[-1] < sma_50.iloc[-1]:
            sentiment = 'BEARISH'
        else:
            sentiment = 'NEUTRAL'
        
        return {
            'volatility': volatility,
            'trend_strength': trend_strength,
            'sentiment': sentiment,
            'favorable_for_breakout': volatility > 0.005 and trend_strength < 0.02
        }
    
    def calculate_stop_loss(self, entry_price: float, signal_type: str) -> float:
        """Calculate stop loss level"""
        pip_value = 0.0001
        
        if signal_type == 'BUY':
            return entry_price - (self.stop_loss_pips * pip_value)
        elif signal_type == 'SELL':
            return entry_price + (self.stop_loss_pips * pip_value)
        
        return entry_price
    
    def calculate_take_profit(self, entry_price: float, stop_loss: float, signal_type: str) -> float:
        """Calculate take profit level"""
        risk = abs(entry_price - stop_loss)
        reward = risk * self.take_profit_ratio
        
        if signal_type == 'BUY':
            return entry_price + reward
        elif signal_type == 'SELL':
            return entry_price - reward
        
        return entry_price
    
    def _no_signal_result(self, reason: str) -> Dict[str, Any]:
        """Return no signal result"""
        return {
            'signal': 'HOLD',
            'confidence': 0.0,
            'entry_price': 0.0,
            'reason': reason,
            'analysis': {
                'strategy': 'London Breakout',
                'status': 'No signal',
                'reason': reason
            }
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': 'London Breakout Strategy',
            'description': 'Trades breakouts during London session opening',
            'parameters': {
                'london_start': str(self.london_start),
                'london_end': str(self.london_end),
                'breakout_period': self.breakout_period,
                'min_range_pips': self.min_range_pips,
                'max_range_pips': self.max_range_pips,
                'stop_loss_pips': self.stop_loss_pips,
                'take_profit_ratio': self.take_profit_ratio
            },
            'market_conditions': 'Works best during London session with moderate volatility',
            'risk_level': 'Medium',
            'timeframe': 'M5-M15',
            'session_dependency': 'London session (8:00-17:00 GMT)'
        }
