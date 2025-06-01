"""
Breakout Reversal Strategy
Identifies false breakouts and trades the reversal
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime

class BreakoutReversalStrategy:
    """Breakout reversal strategy implementation"""
    
    def __init__(self, 
                 support_resistance_period: int = 50,
                 breakout_threshold: float = 0.0015,
                 reversal_confirmation_period: int = 5,
                 volume_confirmation: bool = True,
                 min_consolidation_period: int = 20,
                 stop_loss_pips: float = 20.0,
                 take_profit_pips: float = 40.0):
        
        self.support_resistance_period = support_resistance_period
        self.breakout_threshold = breakout_threshold
        self.reversal_confirmation_period = reversal_confirmation_period
        self.volume_confirmation = volume_confirmation
        self.min_consolidation_period = min_consolidation_period
        self.stop_loss_pips = stop_loss_pips
        self.take_profit_pips = take_profit_pips
        
        self.logger = logging.getLogger(__name__)
        
    def analyze(self, data: pd.DataFrame, symbol: str = "EURUSD") -> Dict[str, Any]:
        """Analyze market for breakout reversal opportunities"""
        try:
            if len(data) < self.support_resistance_period + 20:
                return self._no_signal_result("Insufficient data")
            
            current_price = data['close'].iloc[-1]
            
            support_resistance = self._identify_support_resistance(data)
            
            breakout_analysis = self._analyze_breakout(data, support_resistance)
            
            if not breakout_analysis['breakout_detected']:
                return self._no_signal_result("No breakout detected")
            
            reversal_signal = self._detect_reversal(data, breakout_analysis, support_resistance)
            
            volume_analysis = self._analyze_volume_confirmation(data, breakout_analysis)
            
            return {
                'signal': reversal_signal['signal'],
                'confidence': reversal_signal['confidence'],
                'entry_price': current_price,
                'breakout_type': breakout_analysis['type'],
                'false_breakout': reversal_signal['false_breakout'],
                'support_level': support_resistance['support'],
                'resistance_level': support_resistance['resistance'],
                'volume_confirms': volume_analysis['confirms_reversal'],
                'analysis': {
                    'strategy': 'Breakout Reversal',
                    'consolidation_detected': support_resistance['consolidation'],
                    'breakout_strength': breakout_analysis['strength'],
                    'reversal_probability': reversal_signal['probability'],
                    'market_condition': self._assess_market_condition(data)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in breakout reversal analysis: {e}")
            return self._no_signal_result(f"Analysis error: {e}")
    
    def _identify_support_resistance(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Identify support and resistance levels"""
        
        recent_data = data.tail(self.support_resistance_period)
        
        resistance_level = recent_data['high'].max()
        support_level = recent_data['low'].min()
        
        price_range = resistance_level - support_level
        
        consolidation_threshold = price_range * 0.3
        
        recent_highs = recent_data['high'].tail(self.min_consolidation_period)
        recent_lows = recent_data['low'].tail(self.min_consolidation_period)
        
        high_range = recent_highs.max() - recent_highs.min()
        low_range = recent_lows.max() - recent_lows.min()
        
        consolidation_detected = (high_range < consolidation_threshold and 
                                low_range < consolidation_threshold)
        
        return {
            'support': support_level,
            'resistance': resistance_level,
            'range': price_range,
            'consolidation': consolidation_detected,
            'consolidation_strength': 1.0 - (high_range + low_range) / (2 * price_range)
        }
    
    def _analyze_breakout(self, data: pd.DataFrame, sr_levels: Dict) -> Dict[str, Any]:
        """Analyze breakout characteristics"""
        
        current_price = data['close'].iloc[-1]
        recent_data = data.tail(10)
        
        resistance_level = sr_levels['resistance']
        support_level = sr_levels['support']
        
        upward_breakout = current_price > resistance_level + self.breakout_threshold
        downward_breakout = current_price < support_level - self.breakout_threshold
        
        if upward_breakout:
            breakout_type = 'UPWARD'
            breakout_distance = current_price - resistance_level
            strength = min(breakout_distance / resistance_level, 0.05) * 20
            
        elif downward_breakout:
            breakout_type = 'DOWNWARD'
            breakout_distance = support_level - current_price
            strength = min(breakout_distance / support_level, 0.05) * 20
            
        else:
            return {
                'breakout_detected': False,
                'type': 'NONE',
                'strength': 0.0,
                'distance': 0.0
            }
        
        return {
            'breakout_detected': True,
            'type': breakout_type,
            'strength': strength,
            'distance': breakout_distance,
            'level_broken': resistance_level if upward_breakout else support_level
        }
    
    def _detect_reversal(self, data: pd.DataFrame, breakout_info: Dict, sr_levels: Dict) -> Dict[str, Any]:
        """Detect reversal after breakout"""
        
        if not breakout_info['breakout_detected']:
            return {'signal': 'HOLD', 'confidence': 0.0, 'false_breakout': False}
        
        current_price = data['close'].iloc[-1]
        recent_data = data.tail(self.reversal_confirmation_period)
        
        if breakout_info['type'] == 'UPWARD':
            resistance_level = breakout_info['level_broken']
            
            price_back_below = current_price < resistance_level
            
            recent_rejection = (recent_data['high'].max() > resistance_level and 
                              recent_data['close'].iloc[-1] < resistance_level)
            
            if price_back_below or recent_rejection:
                probability = 0.7
                if recent_rejection:
                    probability += 0.2
                
                return {
                    'signal': 'SELL',
                    'confidence': min(probability, 0.9),
                    'false_breakout': True,
                    'probability': probability,
                    'reversal_type': 'Failed upward breakout'
                }
                
        elif breakout_info['type'] == 'DOWNWARD':
            support_level = breakout_info['level_broken']
            
            price_back_above = current_price > support_level
            
            recent_rejection = (recent_data['low'].min() < support_level and 
                              recent_data['close'].iloc[-1] > support_level)
            
            if price_back_above or recent_rejection:
                probability = 0.7
                if recent_rejection:
                    probability += 0.2
                
                return {
                    'signal': 'BUY',
                    'confidence': min(probability, 0.9),
                    'false_breakout': True,
                    'probability': probability,
                    'reversal_type': 'Failed downward breakout'
                }
        
        return {'signal': 'HOLD', 'confidence': 0.0, 'false_breakout': False}
    
    def _analyze_volume_confirmation(self, data: pd.DataFrame, breakout_info: Dict) -> Dict[str, Any]:
        """Analyze volume for breakout confirmation"""
        
        if not self.volume_confirmation or 'volume' not in data.columns:
            return {'confirms_reversal': True, 'volume_analysis': 'Not available'}
        
        recent_volume = data['volume'].tail(10)
        avg_volume = data['volume'].tail(50).mean()
        
        breakout_volume = recent_volume.iloc[-1]
        
        low_volume_breakout = breakout_volume < avg_volume * 0.8
        
        if low_volume_breakout:
            return {
                'confirms_reversal': True,
                'volume_analysis': 'Low volume breakout - likely false',
                'volume_ratio': breakout_volume / avg_volume
            }
        else:
            return {
                'confirms_reversal': False,
                'volume_analysis': 'High volume breakout - likely genuine',
                'volume_ratio': breakout_volume / avg_volume
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
            return "High volatility - Many false breakouts"
        elif abs(current_price - sma_20) / sma_20 < 0.01:
            return "Consolidation - Good for breakout reversals"
        elif current_price > sma_20 > sma_50:
            return "Uptrend - Watch for resistance breakout failures"
        elif current_price < sma_20 < sma_50:
            return "Downtrend - Watch for support breakout failures"
        else:
            return "Ranging - Ideal for breakout reversal strategy"
    
    def _no_signal_result(self, reason: str) -> Dict[str, Any]:
        """Return no signal result"""
        return {
            'signal': 'HOLD',
            'confidence': 0.0,
            'entry_price': 0.0,
            'reason': reason,
            'analysis': {
                'strategy': 'Breakout Reversal',
                'status': 'No signal',
                'reason': reason
            }
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': 'Breakout Reversal Strategy',
            'description': 'Identifies false breakouts and trades the reversal',
            'parameters': {
                'support_resistance_period': self.support_resistance_period,
                'breakout_threshold': self.breakout_threshold,
                'reversal_confirmation_period': self.reversal_confirmation_period,
                'volume_confirmation': self.volume_confirmation,
                'min_consolidation_period': self.min_consolidation_period,
                'stop_loss_pips': self.stop_loss_pips,
                'take_profit_pips': self.take_profit_pips
            },
            'market_conditions': 'Works best in ranging markets with clear support/resistance',
            'risk_level': 'Medium',
            'timeframe': 'M15-H4',
            'suitable_for': ['ranging_markets', 'false_breakouts'],
            'key_concepts': ['Support/Resistance', 'Volume confirmation', 'Price rejection']
        }
