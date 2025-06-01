"""
Scalping Trading Strategy
High-frequency strategy for quick profits on small price movements
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime

class ScalpingStrategy:
    """Scalping trading strategy implementation"""
    
    def __init__(self, 
                 spread_threshold: float = 0.0002,
                 momentum_period: int = 5,
                 volatility_period: int = 20,
                 min_momentum: float = 0.0001,
                 max_hold_time: int = 15,
                 stop_loss_pips: float = 5.0,
                 take_profit_pips: float = 8.0):
        
        self.spread_threshold = spread_threshold
        self.momentum_period = momentum_period
        self.volatility_period = volatility_period
        self.min_momentum = min_momentum
        self.max_hold_time = max_hold_time
        self.stop_loss_pips = stop_loss_pips
        self.take_profit_pips = take_profit_pips
        
        self.logger = logging.getLogger(__name__)
        
    def analyze(self, data: pd.DataFrame, symbol: str = "EURUSD") -> Dict[str, Any]:
        """Analyze market for scalping opportunities"""
        try:
            if len(data) < 50:
                return self._no_signal_result("Insufficient data")
            
            current_price = data['close'].iloc[-1]
            
            spread_analysis = self._analyze_spread_conditions(data)
            
            if not spread_analysis['suitable']:
                return self._no_signal_result("Spread too wide for scalping")
            
            momentum_analysis = self._analyze_momentum(data)
            volatility_analysis = self._analyze_volatility(data)
            
            scalp_signal = self._generate_scalp_signal(data, momentum_analysis, volatility_analysis)
            
            return {
                'signal': scalp_signal['signal'],
                'confidence': scalp_signal['confidence'],
                'entry_price': current_price,
                'momentum_strength': momentum_analysis['strength'],
                'volatility_level': volatility_analysis['level'],
                'spread_cost': spread_analysis['spread'],
                'analysis': {
                    'strategy': 'Scalping',
                    'momentum_direction': momentum_analysis['direction'],
                    'volatility_suitable': volatility_analysis['suitable'],
                    'market_microstructure': self._assess_microstructure(data),
                    'market_condition': self._assess_market_condition(data)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in scalping analysis: {e}")
            return self._no_signal_result(f"Analysis error: {e}")
    
    def _analyze_spread_conditions(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze spread conditions for scalping"""
        
        if 'bid' in data.columns and 'ask' in data.columns:
            current_spread = data['ask'].iloc[-1] - data['bid'].iloc[-1]
        else:
            recent_high_low = data[['high', 'low']].tail(10)
            avg_spread = (recent_high_low['high'] - recent_high_low['low']).mean()
            current_spread = avg_spread * 0.3
        
        spread_suitable = current_spread <= self.spread_threshold
        
        return {
            'spread': current_spread,
            'suitable': spread_suitable,
            'threshold': self.spread_threshold
        }
    
    def _analyze_momentum(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze short-term momentum"""
        
        momentum_data = data['close'].tail(self.momentum_period)
        
        price_change = momentum_data.iloc[-1] - momentum_data.iloc[0]
        momentum_strength = abs(price_change) / momentum_data.iloc[0]
        
        if price_change > self.min_momentum:
            direction = 'BULLISH'
        elif price_change < -self.min_momentum:
            direction = 'BEARISH'
        else:
            direction = 'NEUTRAL'
        
        ema_fast = data['close'].ewm(span=3).mean()
        ema_slow = data['close'].ewm(span=8).mean()
        
        ema_momentum = 'POSITIVE' if ema_fast.iloc[-1] > ema_slow.iloc[-1] else 'NEGATIVE'
        
        return {
            'direction': direction,
            'strength': momentum_strength,
            'ema_momentum': ema_momentum,
            'price_change': price_change
        }
    
    def _analyze_volatility(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volatility for scalping suitability"""
        
        returns = data['close'].pct_change().dropna()
        current_volatility = returns.tail(self.volatility_period).std()
        
        if current_volatility < 0.002:
            level = 'LOW'
            suitable = False
        elif current_volatility > 0.015:
            level = 'HIGH'
            suitable = False
        else:
            level = 'MODERATE'
            suitable = True
        
        return {
            'level': level,
            'value': current_volatility,
            'suitable': suitable
        }
    
    def _generate_scalp_signal(self, data: pd.DataFrame, momentum_info: Dict, volatility_info: Dict) -> Dict[str, Any]:
        """Generate scalping signal"""
        
        if not volatility_info['suitable']:
            return {'signal': 'HOLD', 'confidence': 0.0}
        
        if momentum_info['strength'] < self.min_momentum:
            return {'signal': 'HOLD', 'confidence': 0.0}
        
        current_price = data['close'].iloc[-1]
        
        sma_5 = data['close'].rolling(5).mean().iloc[-1]
        sma_10 = data['close'].rolling(10).mean().iloc[-1]
        
        confidence = 0.6
        
        if momentum_info['strength'] > self.min_momentum * 2:
            confidence += 0.2
        
        if momentum_info['direction'] == momentum_info['ema_momentum']:
            confidence += 0.1
        
        if momentum_info['direction'] == 'BULLISH' and current_price > sma_5 > sma_10:
            return {
                'signal': 'BUY',
                'confidence': min(confidence, 0.8),
                'scalp_type': 'Momentum breakout'
            }
        elif momentum_info['direction'] == 'BEARISH' and current_price < sma_5 < sma_10:
            return {
                'signal': 'SELL',
                'confidence': min(confidence, 0.8),
                'scalp_type': 'Momentum breakdown'
            }
        
        return {'signal': 'HOLD', 'confidence': 0.0}
    
    def _assess_microstructure(self, data: pd.DataFrame) -> str:
        """Assess market microstructure"""
        
        recent_volumes = data.get('volume', pd.Series([1000] * len(data))).tail(10)
        avg_volume = recent_volumes.mean()
        current_volume = recent_volumes.iloc[-1]
        
        if current_volume > avg_volume * 1.5:
            return "High volume - Good liquidity"
        elif current_volume < avg_volume * 0.5:
            return "Low volume - Poor liquidity"
        else:
            return "Normal volume - Adequate liquidity"
    
    def _assess_market_condition(self, data: pd.DataFrame) -> str:
        """Assess market condition for scalping"""
        if len(data) < 20:
            return "Insufficient data"
        
        returns = data['close'].pct_change().dropna()
        volatility = returns.tail(20).std()
        
        if volatility < 0.002:
            return "Too quiet for scalping"
        elif volatility > 0.015:
            return "Too volatile for scalping"
        else:
            return "Good scalping conditions"
    
    def _no_signal_result(self, reason: str) -> Dict[str, Any]:
        """Return no signal result"""
        return {
            'signal': 'HOLD',
            'confidence': 0.0,
            'entry_price': 0.0,
            'reason': reason,
            'analysis': {
                'strategy': 'Scalping',
                'status': 'No signal',
                'reason': reason
            }
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': 'Scalping Strategy',
            'description': 'High-frequency strategy for quick profits on small moves',
            'parameters': {
                'spread_threshold': self.spread_threshold,
                'momentum_period': self.momentum_period,
                'volatility_period': self.volatility_period,
                'min_momentum': self.min_momentum,
                'max_hold_time': self.max_hold_time,
                'stop_loss_pips': self.stop_loss_pips,
                'take_profit_pips': self.take_profit_pips
            },
            'market_conditions': 'Requires tight spreads and moderate volatility',
            'risk_level': 'Medium',
            'timeframe': 'M1-M5',
            'suitable_for': ['tight_spreads', 'moderate_volatility'],
            'warnings': [
                'Requires fast execution',
                'High transaction costs',
                'Needs constant monitoring'
            ]
        }
