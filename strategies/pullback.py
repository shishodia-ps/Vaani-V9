"""
Pullback Trading Strategy
Identifies and trades pullbacks in trending markets using Fibonacci levels
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime

class PullbackStrategy:
    """Pullback trading strategy implementation"""
    
    def __init__(self, 
                 trend_period: int = 50,
                 pullback_period: int = 20,
                 fib_levels: Optional[List[float]] = None,
                 min_trend_strength: float = 0.6,
                 max_pullback_percent: float = 0.618,
                 stop_loss_pips: float = 25.0,
                 take_profit_pips: float = 50.0):
        
        self.trend_period = trend_period
        self.pullback_period = pullback_period
        self.fib_levels = fib_levels or [0.236, 0.382, 0.5, 0.618, 0.786]
        self.min_trend_strength = min_trend_strength
        self.max_pullback_percent = max_pullback_percent
        self.stop_loss_pips = stop_loss_pips
        self.take_profit_pips = take_profit_pips
        
        self.logger = logging.getLogger(__name__)
        
    def analyze(self, data: pd.DataFrame, symbol: str = "EURUSD") -> Dict[str, Any]:
        """Analyze market for pullback opportunities"""
        try:
            if len(data) < self.trend_period + 20:
                return self._no_signal_result("Insufficient data")
            
            current_price = data['close'].iloc[-1]
            
            trend_analysis = self._analyze_trend(data)
            
            if trend_analysis['strength'] < self.min_trend_strength:
                return self._no_signal_result("Trend not strong enough")
            
            pullback_analysis = self._analyze_pullback(data, trend_analysis)
            
            fibonacci_levels = self._calculate_fibonacci_levels(data, trend_analysis)
            
            entry_signal = self._evaluate_entry_opportunity(data, trend_analysis, pullback_analysis, fibonacci_levels)
            
            return {
                'signal': entry_signal['signal'],
                'confidence': entry_signal['confidence'],
                'entry_price': current_price,
                'trend_direction': trend_analysis['direction'],
                'trend_strength': trend_analysis['strength'],
                'pullback_depth': pullback_analysis['depth_percent'],
                'fibonacci_level': entry_signal.get('fib_level'),
                'analysis': {
                    'strategy': 'Pullback',
                    'trend_confirmed': trend_analysis['confirmed'],
                    'pullback_valid': pullback_analysis['valid'],
                    'support_resistance': fibonacci_levels,
                    'market_condition': self._assess_market_condition(data)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in pullback analysis: {e}")
            return self._no_signal_result(f"Analysis error: {e}")
    
    def _analyze_trend(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the underlying trend"""
        
        sma_20 = data['close'].rolling(20).mean()
        sma_50 = data['close'].rolling(50).mean()
        ema_20 = data['close'].ewm(span=20).mean()
        
        current_price = data['close'].iloc[-1]
        current_sma_20 = sma_20.iloc[-1]
        current_sma_50 = sma_50.iloc[-1]
        current_ema_20 = ema_20.iloc[-1]
        
        trend_data = data.tail(self.trend_period)
        trend_slope = (trend_data['close'].iloc[-1] - trend_data['close'].iloc[0]) / len(trend_data)
        
        if current_price > current_sma_20 > current_sma_50 and trend_slope > 0:
            direction = 'BULLISH'
            strength = min(1.0, abs(trend_slope) * 10000)
        elif current_price < current_sma_20 < current_sma_50 and trend_slope < 0:
            direction = 'BEARISH'
            strength = min(1.0, abs(trend_slope) * 10000)
        else:
            direction = 'SIDEWAYS'
            strength = 0.0
        
        ma_alignment_score = 0
        if direction == 'BULLISH':
            if current_price > current_ema_20:
                ma_alignment_score += 0.3
            if current_sma_20 > current_sma_50:
                ma_alignment_score += 0.3
        elif direction == 'BEARISH':
            if current_price < current_ema_20:
                ma_alignment_score += 0.3
            if current_sma_20 < current_sma_50:
                ma_alignment_score += 0.3
        
        strength += ma_alignment_score
        
        confirmed = strength >= self.min_trend_strength and direction != 'SIDEWAYS'
        
        return {
            'direction': direction,
            'strength': min(strength, 1.0),
            'confirmed': confirmed,
            'slope': trend_slope
        }
    
    def _analyze_pullback(self, data: pd.DataFrame, trend_info: Dict) -> Dict[str, Any]:
        """Analyze pullback characteristics"""
        
        if not trend_info['confirmed']:
            return {'valid': False, 'depth_percent': 0}
        
        recent_data = data.tail(self.pullback_period)
        
        if trend_info['direction'] == 'BULLISH':
            trend_high = data.tail(self.trend_period)['high'].max()
            recent_low = recent_data['low'].min()
            pullback_depth = (trend_high - recent_low) / trend_high
            
            current_price = data['close'].iloc[-1]
            pullback_from_high = (trend_high - current_price) / trend_high
            
        elif trend_info['direction'] == 'BEARISH':
            trend_low = data.tail(self.trend_period)['low'].min()
            recent_high = recent_data['high'].max()
            pullback_depth = (recent_high - trend_low) / trend_low
            
            current_price = data['close'].iloc[-1]
            pullback_from_low = (current_price - trend_low) / trend_low
            pullback_from_high = pullback_from_low
        else:
            return {'valid': False, 'depth_percent': 0}
        
        valid_pullback = 0.1 < pullback_depth < self.max_pullback_percent
        
        return {
            'valid': valid_pullback,
            'depth_percent': pullback_depth,
            'pullback_from_extreme': pullback_from_high
        }
    
    def _calculate_fibonacci_levels(self, data: pd.DataFrame, trend_info: Dict) -> Dict[str, float]:
        """Calculate Fibonacci retracement levels"""
        
        if not trend_info['confirmed']:
            return {}
        
        trend_data = data.tail(self.trend_period)
        
        if trend_info['direction'] == 'BULLISH':
            swing_low = trend_data['low'].min()
            swing_high = trend_data['high'].max()
            price_range = swing_high - swing_low
            
            fib_levels = {}
            for level in self.fib_levels:
                fib_levels[f"fib_{level}"] = swing_high - (price_range * level)
                
        elif trend_info['direction'] == 'BEARISH':
            swing_high = trend_data['high'].max()
            swing_low = trend_data['low'].min()
            price_range = swing_high - swing_low
            
            fib_levels = {}
            for level in self.fib_levels:
                fib_levels[f"fib_{level}"] = swing_low + (price_range * level)
        else:
            fib_levels = {}
        
        return fib_levels
    
    def _evaluate_entry_opportunity(self, data: pd.DataFrame, trend_info: Dict, 
                                  pullback_info: Dict, fib_levels: Dict) -> Dict[str, Any]:
        """Evaluate entry opportunity at Fibonacci levels"""
        
        if not trend_info['confirmed'] or not pullback_info['valid']:
            return {'signal': 'HOLD', 'confidence': 0.0}
        
        current_price = data['close'].iloc[-1]
        
        best_fib_level = None
        min_distance = float('inf')
        
        for level_name, level_price in fib_levels.items():
            distance = abs(current_price - level_price) / current_price
            if distance < min_distance and distance < 0.001:
                min_distance = distance
                best_fib_level = level_name
        
        if best_fib_level is None:
            return {'signal': 'HOLD', 'confidence': 0.0}
        
        rsi = self._calculate_rsi(data)
        current_rsi = rsi.iloc[-1] if len(rsi) > 0 else 50
        
        confidence = 0.6
        
        if trend_info['strength'] > 0.8:
            confidence += 0.2
        
        if 0.3 < pullback_info['depth_percent'] < 0.6:
            confidence += 0.1
        
        if trend_info['direction'] == 'BULLISH':
            if current_rsi < 50 and best_fib_level in ['fib_0.382', 'fib_0.5', 'fib_0.618']:
                return {
                    'signal': 'BUY',
                    'confidence': min(confidence, 0.9),
                    'fib_level': best_fib_level,
                    'entry_reason': f"Bullish pullback at {best_fib_level}"
                }
        elif trend_info['direction'] == 'BEARISH':
            if current_rsi > 50 and best_fib_level in ['fib_0.382', 'fib_0.5', 'fib_0.618']:
                return {
                    'signal': 'SELL',
                    'confidence': min(confidence, 0.9),
                    'fib_level': best_fib_level,
                    'entry_reason': f"Bearish pullback at {best_fib_level}"
                }
        
        return {'signal': 'HOLD', 'confidence': 0.0}
    
    def _calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _assess_market_condition(self, data: pd.DataFrame) -> str:
        """Assess current market condition"""
        if len(data) < 50:
            return "Insufficient data"
        
        returns = data['close'].pct_change().dropna()
        volatility = returns.tail(20).std()
        
        sma_20 = data['close'].rolling(20).mean().iloc[-1]
        sma_50 = data['close'].rolling(50).mean().iloc[-1]
        current_price = data['close'].iloc[-1]
        
        if volatility > 0.015:
            return "High volatility - Pullbacks may be deeper"
        elif current_price > sma_20 > sma_50:
            return "Uptrend - Look for bullish pullbacks"
        elif current_price < sma_20 < sma_50:
            return "Downtrend - Look for bearish pullbacks"
        else:
            return "Ranging - Limited pullback opportunities"
    
    def _no_signal_result(self, reason: str) -> Dict[str, Any]:
        """Return no signal result"""
        return {
            'signal': 'HOLD',
            'confidence': 0.0,
            'entry_price': 0.0,
            'reason': reason,
            'analysis': {
                'strategy': 'Pullback',
                'status': 'No signal',
                'reason': reason
            }
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': 'Pullback Strategy',
            'description': 'Trades pullbacks in trending markets using Fibonacci levels',
            'parameters': {
                'trend_period': self.trend_period,
                'pullback_period': self.pullback_period,
                'fib_levels': self.fib_levels,
                'min_trend_strength': self.min_trend_strength,
                'max_pullback_percent': self.max_pullback_percent,
                'stop_loss_pips': self.stop_loss_pips,
                'take_profit_pips': self.take_profit_pips
            },
            'market_conditions': 'Works best in trending markets with clear pullbacks',
            'risk_level': 'Medium',
            'timeframe': 'H1-H4',
            'suitable_for': ['trending_markets', 'fibonacci_trading'],
            'key_levels': 'Fibonacci retracement levels (38.2%, 50%, 61.8%)'
        }
