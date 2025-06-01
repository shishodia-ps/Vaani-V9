"""
New York Reversal Trading Strategy
Looks for reversals during NY session open (8:00-10:00 EST)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, time

class NYReversalStrategy:
    """New York session reversal trading strategy"""
    
    def __init__(self, 
                 ny_open_hour: int = 8,
                 ny_close_hour: int = 10,
                 min_range_pips: float = 15.0,
                 max_range_pips: float = 50.0,
                 reversal_threshold: float = 0.618,
                 stop_loss_pips: float = 25.0,
                 take_profit_pips: float = 40.0):
        
        self.ny_open_hour = ny_open_hour
        self.ny_close_hour = ny_close_hour
        self.min_range_pips = min_range_pips
        self.max_range_pips = max_range_pips
        self.reversal_threshold = reversal_threshold
        self.stop_loss_pips = stop_loss_pips
        self.take_profit_pips = take_profit_pips
        
        self.logger = logging.getLogger(__name__)
        self.session_high = None
        self.session_low = None
        self.session_range = 0.0
        
    def analyze(self, data: pd.DataFrame, symbol: str = "EURUSD") -> Dict[str, Any]:
        """Analyze market for NY reversal opportunities"""
        try:
            if len(data) < 100:
                return self._no_signal_result("Insufficient data")
            
            current_time = datetime.now().time()
            current_price = data['close'].iloc[-1]
            
            session_analysis = self._analyze_ny_session(data, current_time)
            
            if not session_analysis['in_session']:
                return self._no_signal_result("Outside NY session hours")
            
            reversal_signal = self._detect_reversal_pattern(data, session_analysis)
            
            momentum_analysis = self._analyze_momentum(data)
            
            return {
                'signal': reversal_signal['signal'],
                'confidence': reversal_signal['confidence'],
                'entry_price': current_price,
                'session_high': session_analysis['session_high'],
                'session_low': session_analysis['session_low'],
                'session_range': session_analysis['range_pips'],
                'reversal_level': reversal_signal.get('reversal_level'),
                'analysis': {
                    'strategy': 'NY Reversal',
                    'session_time': session_analysis['session_time'],
                    'range_suitable': session_analysis['range_suitable'],
                    'momentum_direction': momentum_analysis['direction'],
                    'momentum_strength': momentum_analysis['strength'],
                    'market_condition': self._assess_market_condition(data)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in NY reversal analysis: {e}")
            return self._no_signal_result(f"Analysis error: {e}")
    
    def _analyze_ny_session(self, data: pd.DataFrame, current_time: time) -> Dict[str, Any]:
        """Analyze NY session characteristics"""
        
        current_hour = current_time.hour
        in_session = self.ny_open_hour <= current_hour < self.ny_close_hour
        
        if not in_session:
            return {
                'in_session': False,
                'session_time': 'Outside NY hours',
                'session_high': None,
                'session_low': None,
                'range_pips': 0,
                'range_suitable': False
            }
        
        recent_data = data.tail(120)
        
        session_high = recent_data['high'].max()
        session_low = recent_data['low'].min()
        range_pips = (session_high - session_low) * 10000
        
        range_suitable = self.min_range_pips <= range_pips <= self.max_range_pips
        
        self.session_high = session_high
        self.session_low = session_low
        self.session_range = range_pips
        
        session_progress = (current_hour - self.ny_open_hour) / (self.ny_close_hour - self.ny_open_hour)
        
        return {
            'in_session': True,
            'session_time': f"NY Hour {current_hour}",
            'session_high': session_high,
            'session_low': session_low,
            'range_pips': range_pips,
            'range_suitable': range_suitable,
            'session_progress': session_progress
        }
    
    def _detect_reversal_pattern(self, data: pd.DataFrame, session_info: Dict) -> Dict[str, Any]:
        """Detect reversal patterns within NY session"""
        
        if not session_info['range_suitable']:
            return {'signal': 'HOLD', 'confidence': 0.0}
        
        current_price = data['close'].iloc[-1]
        session_high = session_info['session_high']
        session_low = session_info['session_low']
        session_range = session_high - session_low
        
        upper_reversal_level = session_high - (session_range * (1 - self.reversal_threshold))
        lower_reversal_level = session_low + (session_range * (1 - self.reversal_threshold))
        
        recent_prices = data['close'].tail(10)
        price_momentum = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]
        
        confidence = 0.5
        
        if session_info['session_progress'] > 0.3:
            confidence += 0.2
        
        if abs(price_momentum) > 0.001:
            confidence += 0.1
        
        if current_price >= upper_reversal_level and price_momentum > 0:
            return {
                'signal': 'SELL',
                'confidence': min(confidence + 0.2, 0.9),
                'reversal_level': upper_reversal_level,
                'pattern': 'Upper reversal'
            }
        elif current_price <= lower_reversal_level and price_momentum < 0:
            return {
                'signal': 'BUY',
                'confidence': min(confidence + 0.2, 0.9),
                'reversal_level': lower_reversal_level,
                'pattern': 'Lower reversal'
            }
        
        return {'signal': 'HOLD', 'confidence': 0.0}
    
    def _analyze_momentum(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price momentum"""
        
        if len(data) < 20:
            return {'direction': 'Unknown', 'strength': 0.0}
        
        short_ma = data['close'].rolling(5).mean()
        long_ma = data['close'].rolling(20).mean()
        
        current_short = short_ma.iloc[-1]
        current_long = long_ma.iloc[-1]
        
        if current_short > current_long:
            direction = 'Bullish'
        elif current_short < current_long:
            direction = 'Bearish'
        else:
            direction = 'Neutral'
        
        momentum_strength = abs(current_short - current_long) / current_long
        
        return {
            'direction': direction,
            'strength': momentum_strength
        }
    
    def _assess_market_condition(self, data: pd.DataFrame) -> str:
        """Assess current market condition"""
        if len(data) < 50:
            return "Insufficient data"
        
        returns = data['close'].pct_change().dropna()
        volatility = returns.tail(20).std()
        
        if volatility > 0.015:
            return "High volatility - Good for reversals"
        elif volatility < 0.005:
            return "Low volatility - Limited reversal potential"
        else:
            return "Moderate volatility - Suitable for reversals"
    
    def _no_signal_result(self, reason: str) -> Dict[str, Any]:
        """Return no signal result"""
        return {
            'signal': 'HOLD',
            'confidence': 0.0,
            'entry_price': 0.0,
            'reason': reason,
            'analysis': {
                'strategy': 'NY Reversal',
                'status': 'No signal',
                'reason': reason
            }
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': 'New York Reversal Strategy',
            'description': 'Trades reversals during NY session open hours',
            'parameters': {
                'ny_open_hour': self.ny_open_hour,
                'ny_close_hour': self.ny_close_hour,
                'min_range_pips': self.min_range_pips,
                'max_range_pips': self.max_range_pips,
                'reversal_threshold': self.reversal_threshold,
                'stop_loss_pips': self.stop_loss_pips,
                'take_profit_pips': self.take_profit_pips
            },
            'market_conditions': 'Works best during NY session with moderate volatility',
            'risk_level': 'Medium',
            'timeframe': 'M15-H1',
            'suitable_for': ['session_trading', 'reversal_patterns'],
            'active_hours': 'NY Session (8:00-10:00 EST)'
        }
