"""
Trend Following Strategy
Classic trend following using multiple timeframe analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime

class TrendFollowingStrategy:
    """Trend following strategy implementation"""
    
    def __init__(self, 
                 fast_ma_period: int = 20,
                 slow_ma_period: int = 50,
                 trend_strength_period: int = 100,
                 atr_period: int = 14,
                 min_trend_strength: float = 0.6,
                 breakout_threshold: float = 1.5,
                 stop_loss_atr_multiplier: float = 2.0,
                 take_profit_atr_multiplier: float = 3.0):
        
        self.fast_ma_period = fast_ma_period
        self.slow_ma_period = slow_ma_period
        self.trend_strength_period = trend_strength_period
        self.atr_period = atr_period
        self.min_trend_strength = min_trend_strength
        self.breakout_threshold = breakout_threshold
        self.stop_loss_atr_multiplier = stop_loss_atr_multiplier
        self.take_profit_atr_multiplier = take_profit_atr_multiplier
        
        self.logger = logging.getLogger(__name__)
        
    def analyze(self, data: pd.DataFrame, symbol: str = "EURUSD") -> Dict[str, Any]:
        """Analyze market for trend following opportunities"""
        try:
            if len(data) < self.trend_strength_period:
                return self._no_signal_result("Insufficient data")
            
            current_price = data['close'].iloc[-1]
            
            trend_analysis = self._analyze_trend_strength(data)
            momentum_analysis = self._analyze_momentum(data)
            breakout_analysis = self._analyze_breakout(data)
            
            atr = self._calculate_atr(data)
            
            trend_signal = self._generate_trend_signal(data, trend_analysis, momentum_analysis, breakout_analysis)
            
            position_sizing = self._calculate_position_sizing(atr, trend_analysis)
            
            return {
                'signal': trend_signal['signal'],
                'confidence': trend_signal['confidence'],
                'entry_price': current_price,
                'trend_direction': trend_analysis['direction'],
                'trend_strength': trend_analysis['strength'],
                'momentum_score': momentum_analysis['score'],
                'breakout_strength': breakout_analysis['strength'],
                'atr_value': atr,
                'position_sizing': position_sizing,
                'analysis': {
                    'strategy': 'Trend Following',
                    'trend_confirmed': trend_analysis['confirmed'],
                    'momentum_aligned': momentum_analysis['aligned'],
                    'breakout_detected': breakout_analysis['detected'],
                    'market_condition': self._assess_market_condition(data)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in trend following analysis: {e}")
            return self._no_signal_result(f"Analysis error: {e}")
    
    def _analyze_trend_strength(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trend strength using multiple indicators"""
        
        sma_fast = data['close'].rolling(self.fast_ma_period).mean()
        sma_slow = data['close'].rolling(self.slow_ma_period).mean()
        ema_fast = data['close'].ewm(span=self.fast_ma_period).mean()
        
        current_price = data['close'].iloc[-1]
        current_sma_fast = sma_fast.iloc[-1]
        current_sma_slow = sma_slow.iloc[-1]
        current_ema_fast = ema_fast.iloc[-1]
        
        trend_data = data.tail(self.trend_strength_period)
        
        if current_price > current_sma_fast > current_sma_slow:
            direction = 'BULLISH'
            ma_score = 0.4
        elif current_price < current_sma_fast < current_sma_slow:
            direction = 'BEARISH'
            ma_score = 0.4
        else:
            direction = 'SIDEWAYS'
            ma_score = 0.0
        
        price_vs_ema = abs(current_price - current_ema_fast) / current_ema_fast
        ema_score = min(price_vs_ema * 100, 0.3)
        
        trend_slope = (trend_data['close'].iloc[-1] - trend_data['close'].iloc[0]) / len(trend_data)
        slope_score = min(abs(trend_slope) * 1000, 0.3)
        
        strength = ma_score + ema_score + slope_score
        confirmed = strength >= self.min_trend_strength and direction != 'SIDEWAYS'
        
        return {
            'direction': direction,
            'strength': min(strength, 1.0),
            'confirmed': confirmed,
            'ma_alignment': ma_score > 0,
            'slope': trend_slope
        }
    
    def _analyze_momentum(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze momentum indicators"""
        
        rsi = self._calculate_rsi(data)
        macd_line, macd_signal, macd_histogram = self._calculate_macd(data)
        
        current_rsi = rsi.iloc[-1] if len(rsi) > 0 else 50
        current_macd = macd_line.iloc[-1] if len(macd_line) > 0 else 0
        current_macd_signal = macd_signal.iloc[-1] if len(macd_signal) > 0 else 0
        
        momentum_score = 0.0
        
        if 30 < current_rsi < 70:
            momentum_score += 0.3
        elif current_rsi > 70:
            momentum_score += 0.1
        elif current_rsi < 30:
            momentum_score += 0.1
        
        if current_macd > current_macd_signal:
            momentum_score += 0.3
            macd_direction = 'POSITIVE'
        else:
            macd_direction = 'NEGATIVE'
        
        price_momentum = (data['close'].iloc[-1] - data['close'].iloc[-10]) / data['close'].iloc[-10]
        if abs(price_momentum) > 0.001:
            momentum_score += 0.2
        
        aligned = momentum_score > 0.5
        
        return {
            'score': momentum_score,
            'aligned': aligned,
            'rsi': current_rsi,
            'macd_direction': macd_direction,
            'price_momentum': price_momentum
        }
    
    def _analyze_breakout(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze breakout patterns"""
        
        recent_data = data.tail(20)
        
        resistance_level = recent_data['high'].max()
        support_level = recent_data['low'].min()
        
        current_price = data['close'].iloc[-1]
        
        resistance_distance = (current_price - resistance_level) / resistance_level
        support_distance = (support_level - current_price) / current_price
        
        atr = self._calculate_atr(data)
        
        if resistance_distance > 0 and resistance_distance > (atr * self.breakout_threshold):
            breakout_type = 'UPWARD'
            strength = min(resistance_distance / atr, 3.0)
            detected = True
        elif support_distance > 0 and support_distance > (atr * self.breakout_threshold):
            breakout_type = 'DOWNWARD'
            strength = min(support_distance / atr, 3.0)
            detected = True
        else:
            breakout_type = 'NONE'
            strength = 0.0
            detected = False
        
        return {
            'detected': detected,
            'type': breakout_type,
            'strength': strength,
            'resistance_level': resistance_level,
            'support_level': support_level
        }
    
    def _generate_trend_signal(self, data: pd.DataFrame, trend_info: Dict, momentum_info: Dict, breakout_info: Dict) -> Dict[str, Any]:
        """Generate trend following signal"""
        
        if not trend_info['confirmed']:
            return {'signal': 'HOLD', 'confidence': 0.0}
        
        confidence = 0.5
        
        if trend_info['strength'] > 0.8:
            confidence += 0.2
        
        if momentum_info['aligned']:
            confidence += 0.2
        
        if breakout_info['detected']:
            confidence += 0.1
        
        if trend_info['direction'] == 'BULLISH':
            if momentum_info['score'] > 0.5:
                return {
                    'signal': 'BUY',
                    'confidence': min(confidence, 0.9),
                    'signal_type': 'Trend continuation'
                }
        elif trend_info['direction'] == 'BEARISH':
            if momentum_info['score'] > 0.5:
                return {
                    'signal': 'SELL',
                    'confidence': min(confidence, 0.9),
                    'signal_type': 'Trend continuation'
                }
        
        return {'signal': 'HOLD', 'confidence': 0.0}
    
    def _calculate_atr(self, data: pd.DataFrame) -> float:
        """Calculate Average True Range"""
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift())
        low_close = abs(data['low'] - data['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=self.atr_period).mean().iloc[-1]
        
        return atr if not pd.isna(atr) else 0.001
    
    def _calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD indicator"""
        ema_12 = data['close'].ewm(span=12).mean()
        ema_26 = data['close'].ewm(span=26).mean()
        macd_line = ema_12 - ema_26
        macd_signal = macd_line.ewm(span=9).mean()
        macd_histogram = macd_line - macd_signal
        
        return macd_line, macd_signal, macd_histogram
    
    def _calculate_position_sizing(self, atr: float, trend_info: Dict) -> Dict[str, Any]:
        """Calculate position sizing based on ATR and trend strength"""
        
        base_risk = 0.01
        
        if trend_info['strength'] > 0.8:
            risk_multiplier = 1.5
        elif trend_info['strength'] > 0.6:
            risk_multiplier = 1.2
        else:
            risk_multiplier = 1.0
        
        adjusted_risk = base_risk * risk_multiplier
        
        stop_loss_distance = atr * self.stop_loss_atr_multiplier
        take_profit_distance = atr * self.take_profit_atr_multiplier
        
        return {
            'risk_percent': adjusted_risk,
            'stop_loss_distance': stop_loss_distance,
            'take_profit_distance': take_profit_distance,
            'risk_reward_ratio': take_profit_distance / stop_loss_distance
        }
    
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
            return "High volatility - Strong trends possible"
        elif current_price > sma_20 > sma_50:
            return "Uptrend - Follow bullish momentum"
        elif current_price < sma_20 < sma_50:
            return "Downtrend - Follow bearish momentum"
        else:
            return "Ranging - Wait for trend emergence"
    
    def _no_signal_result(self, reason: str) -> Dict[str, Any]:
        """Return no signal result"""
        return {
            'signal': 'HOLD',
            'confidence': 0.0,
            'entry_price': 0.0,
            'reason': reason,
            'analysis': {
                'strategy': 'Trend Following',
                'status': 'No signal',
                'reason': reason
            }
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': 'Trend Following Strategy',
            'description': 'Classic trend following using multiple timeframe analysis',
            'parameters': {
                'fast_ma_period': self.fast_ma_period,
                'slow_ma_period': self.slow_ma_period,
                'trend_strength_period': self.trend_strength_period,
                'atr_period': self.atr_period,
                'min_trend_strength': self.min_trend_strength,
                'breakout_threshold': self.breakout_threshold,
                'stop_loss_atr_multiplier': self.stop_loss_atr_multiplier,
                'take_profit_atr_multiplier': self.take_profit_atr_multiplier
            },
            'market_conditions': 'Works best in trending markets with clear direction',
            'risk_level': 'Medium',
            'timeframe': 'H1-D1',
            'suitable_for': ['trending_markets', 'momentum_trading'],
            'indicators': ['Moving Averages', 'RSI', 'MACD', 'ATR']
        }
