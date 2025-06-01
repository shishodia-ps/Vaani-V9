"""
Stochastic Strategy
Strategy using Stochastic Oscillator for overbought/oversold conditions
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime

class StochasticStrategy:
    """Stochastic oscillator trading strategy"""
    
    def __init__(self, 
                 k_period: int = 14,
                 d_period: int = 3,
                 smooth_k: int = 3,
                 overbought_level: float = 80.0,
                 oversold_level: float = 20.0,
                 divergence_lookback: int = 20,
                 stop_loss_pips: float = 25.0,
                 take_profit_pips: float = 40.0):
        
        self.k_period = k_period
        self.d_period = d_period
        self.smooth_k = smooth_k
        self.overbought_level = overbought_level
        self.oversold_level = oversold_level
        self.divergence_lookback = divergence_lookback
        self.stop_loss_pips = stop_loss_pips
        self.take_profit_pips = take_profit_pips
        
        self.logger = logging.getLogger(__name__)
        
    def analyze(self, data: pd.DataFrame, symbol: str = "EURUSD") -> Dict[str, Any]:
        """Analyze market using Stochastic oscillator"""
        try:
            if len(data) < self.k_period + self.d_period + 10:
                return self._no_signal_result("Insufficient data")
            
            current_price = data['close'].iloc[-1]
            
            stoch_data = self._calculate_stochastic(data)
            
            signal_analysis = self._analyze_stochastic_signals(data, stoch_data)
            
            divergence_analysis = self._detect_divergences(data, stoch_data)
            
            crossover_analysis = self._analyze_crossovers(stoch_data)
            
            final_signal = self._generate_final_signal(signal_analysis, divergence_analysis, crossover_analysis)
            
            return {
                'signal': final_signal['signal'],
                'confidence': final_signal['confidence'],
                'entry_price': current_price,
                'stoch_k': stoch_data['%K'].iloc[-1],
                'stoch_d': stoch_data['%D'].iloc[-1],
                'overbought': signal_analysis['overbought'],
                'oversold': signal_analysis['oversold'],
                'divergence_detected': divergence_analysis['detected'],
                'crossover_signal': crossover_analysis['signal'],
                'analysis': {
                    'strategy': 'Stochastic',
                    'stoch_level': signal_analysis['level'],
                    'trend_alignment': signal_analysis['trend_aligned'],
                    'signal_strength': final_signal['strength'],
                    'market_condition': self._assess_market_condition(data)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in stochastic analysis: {e}")
            return self._no_signal_result(f"Analysis error: {e}")
    
    def _calculate_stochastic(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Stochastic oscillator"""
        
        stoch_data = data.copy()
        
        lowest_low = stoch_data['low'].rolling(window=self.k_period).min()
        highest_high = stoch_data['high'].rolling(window=self.k_period).max()
        
        raw_k = 100 * ((stoch_data['close'] - lowest_low) / (highest_high - lowest_low))
        
        stoch_data['%K'] = raw_k.rolling(window=self.smooth_k).mean()
        
        stoch_data['%D'] = stoch_data['%K'].rolling(window=self.d_period).mean()
        
        return stoch_data
    
    def _analyze_stochastic_signals(self, data: pd.DataFrame, stoch_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze stochastic signals"""
        
        current_k = stoch_data['%K'].iloc[-1]
        current_d = stoch_data['%D'].iloc[-1]
        
        overbought = current_k > self.overbought_level and current_d > self.overbought_level
        oversold = current_k < self.oversold_level and current_d < self.oversold_level
        
        if overbought:
            level = 'OVERBOUGHT'
        elif oversold:
            level = 'OVERSOLD'
        elif current_k > 50:
            level = 'BULLISH'
        else:
            level = 'BEARISH'
        
        sma_20 = data['close'].rolling(20).mean().iloc[-1]
        current_price = data['close'].iloc[-1]
        
        trend_aligned = False
        if level == 'OVERSOLD' and current_price > sma_20:
            trend_aligned = True
        elif level == 'OVERBOUGHT' and current_price < sma_20:
            trend_aligned = True
        
        return {
            'overbought': overbought,
            'oversold': oversold,
            'level': level,
            'k_value': current_k,
            'd_value': current_d,
            'trend_aligned': trend_aligned
        }
    
    def _detect_divergences(self, data: pd.DataFrame, stoch_data: pd.DataFrame) -> Dict[str, Any]:
        """Detect price-stochastic divergences"""
        
        if len(stoch_data) < self.divergence_lookback:
            return {'detected': False, 'type': None}
        
        recent_data = stoch_data.tail(self.divergence_lookback)
        
        price_highs = self._find_peaks(np.array(recent_data['high'].values))
        price_lows = self._find_troughs(np.array(recent_data['low'].values))
        stoch_highs = self._find_peaks(np.array(recent_data['%K'].values))
        stoch_lows = self._find_troughs(np.array(recent_data['%K'].values))
        
        bullish_divergence = self._check_bullish_divergence(recent_data, price_lows, stoch_lows)
        bearish_divergence = self._check_bearish_divergence(recent_data, price_highs, stoch_highs)
        
        if bullish_divergence:
            return {'detected': True, 'type': 'BULLISH', 'strength': bullish_divergence}
        elif bearish_divergence:
            return {'detected': True, 'type': 'BEARISH', 'strength': bearish_divergence}
        else:
            return {'detected': False, 'type': None}
    
    def _find_peaks(self, data) -> List[int]:
        """Find peaks in data"""
        peaks = []
        for i in range(2, len(data) - 2):
            if data[i] > data[i-1] and data[i] > data[i+1] and data[i] > data[i-2] and data[i] > data[i+2]:
                peaks.append(i)
        return peaks
    
    def _find_troughs(self, data: np.ndarray) -> List[int]:
        """Find troughs in data"""
        troughs = []
        for i in range(2, len(data) - 2):
            if data[i] < data[i-1] and data[i] < data[i+1] and data[i] < data[i-2] and data[i] < data[i+2]:
                troughs.append(i)
        return troughs
    
    def _check_bullish_divergence(self, data: pd.DataFrame, price_lows: List[int], stoch_lows: List[int]) -> Optional[float]:
        """Check for bullish divergence"""
        if len(price_lows) < 2 or len(stoch_lows) < 2:
            return None
        
        last_price_lows = sorted(price_lows)[-2:]
        
        if len(last_price_lows) < 2:
            return None
        
        price_1 = data['low'].iloc[last_price_lows[0]]
        price_2 = data['low'].iloc[last_price_lows[1]]
        
        nearest_stoch_1 = min(stoch_lows, key=lambda x: abs(x - last_price_lows[0]))
        nearest_stoch_2 = min(stoch_lows, key=lambda x: abs(x - last_price_lows[1]))
        
        stoch_1 = data['%K'].iloc[nearest_stoch_1]
        stoch_2 = data['%K'].iloc[nearest_stoch_2]
        
        if price_2 < price_1 and stoch_2 > stoch_1:
            strength = abs(price_2 - price_1) / price_1 + abs(stoch_2 - stoch_1) / 100
            return min(strength * 5, 1.0)
        
        return None
    
    def _check_bearish_divergence(self, data: pd.DataFrame, price_highs: List[int], stoch_highs: List[int]) -> Optional[float]:
        """Check for bearish divergence"""
        if len(price_highs) < 2 or len(stoch_highs) < 2:
            return None
        
        last_price_highs = sorted(price_highs)[-2:]
        
        if len(last_price_highs) < 2:
            return None
        
        price_1 = data['high'].iloc[last_price_highs[0]]
        price_2 = data['high'].iloc[last_price_highs[1]]
        
        nearest_stoch_1 = min(stoch_highs, key=lambda x: abs(x - last_price_highs[0]))
        nearest_stoch_2 = min(stoch_highs, key=lambda x: abs(x - last_price_highs[1]))
        
        stoch_1 = data['%K'].iloc[nearest_stoch_1]
        stoch_2 = data['%K'].iloc[nearest_stoch_2]
        
        if price_2 > price_1 and stoch_2 < stoch_1:
            strength = abs(price_2 - price_1) / price_1 + abs(stoch_2 - stoch_1) / 100
            return min(strength * 5, 1.0)
        
        return None
    
    def _analyze_crossovers(self, stoch_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze %K and %D crossovers"""
        
        if len(stoch_data) < 5:
            return {'signal': 'NONE', 'strength': 0.0}
        
        recent_k = stoch_data['%K'].tail(3)
        recent_d = stoch_data['%D'].tail(3)
        
        current_k = recent_k.iloc[-1]
        current_d = recent_d.iloc[-1]
        prev_k = recent_k.iloc[-2]
        prev_d = recent_d.iloc[-2]
        
        bullish_crossover = prev_k <= prev_d and current_k > current_d
        bearish_crossover = prev_k >= prev_d and current_k < current_d
        
        if bullish_crossover and current_k < self.oversold_level + 10:
            return {'signal': 'BULLISH_CROSSOVER', 'strength': 0.8}
        elif bearish_crossover and current_k > self.overbought_level - 10:
            return {'signal': 'BEARISH_CROSSOVER', 'strength': 0.8}
        elif bullish_crossover:
            return {'signal': 'BULLISH_CROSSOVER', 'strength': 0.5}
        elif bearish_crossover:
            return {'signal': 'BEARISH_CROSSOVER', 'strength': 0.5}
        else:
            return {'signal': 'NONE', 'strength': 0.0}
    
    def _generate_final_signal(self, signal_info: Dict, divergence_info: Dict, crossover_info: Dict) -> Dict[str, Any]:
        """Generate final trading signal"""
        
        confidence = 0.5
        signal = 'HOLD'
        strength = 0.0
        
        if signal_info['oversold'] and crossover_info['signal'] == 'BULLISH_CROSSOVER':
            signal = 'BUY'
            confidence = 0.7
            strength = crossover_info['strength']
            
        elif signal_info['overbought'] and crossover_info['signal'] == 'BEARISH_CROSSOVER':
            signal = 'SELL'
            confidence = 0.7
            strength = crossover_info['strength']
        
        if divergence_info['detected']:
            if divergence_info['type'] == 'BULLISH' and signal_info['oversold']:
                signal = 'BUY'
                confidence += 0.2
                strength += divergence_info.get('strength', 0.5)
            elif divergence_info['type'] == 'BEARISH' and signal_info['overbought']:
                signal = 'SELL'
                confidence += 0.2
                strength += divergence_info.get('strength', 0.5)
        
        if signal_info['trend_aligned']:
            confidence += 0.1
        
        return {
            'signal': signal,
            'confidence': min(confidence, 0.9),
            'strength': min(strength, 1.0)
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
            return "High volatility - Stochastic signals may be noisy"
        elif current_price > sma_20 > sma_50:
            return "Uptrend - Look for oversold bounces"
        elif current_price < sma_20 < sma_50:
            return "Downtrend - Look for overbought reversals"
        else:
            return "Ranging - Ideal for stochastic strategy"
    
    def _no_signal_result(self, reason: str) -> Dict[str, Any]:
        """Return no signal result"""
        return {
            'signal': 'HOLD',
            'confidence': 0.0,
            'entry_price': 0.0,
            'reason': reason,
            'analysis': {
                'strategy': 'Stochastic',
                'status': 'No signal',
                'reason': reason
            }
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': 'Stochastic Strategy',
            'description': 'Uses Stochastic Oscillator for overbought/oversold conditions',
            'parameters': {
                'k_period': self.k_period,
                'd_period': self.d_period,
                'smooth_k': self.smooth_k,
                'overbought_level': self.overbought_level,
                'oversold_level': self.oversold_level,
                'divergence_lookback': self.divergence_lookback,
                'stop_loss_pips': self.stop_loss_pips,
                'take_profit_pips': self.take_profit_pips
            },
            'market_conditions': 'Works best in ranging markets',
            'risk_level': 'Medium',
            'timeframe': 'M15-H4',
            'suitable_for': ['ranging_markets', 'overbought_oversold'],
            'indicators': ['Stochastic %K', 'Stochastic %D', 'Divergences', 'Crossovers']
        }
