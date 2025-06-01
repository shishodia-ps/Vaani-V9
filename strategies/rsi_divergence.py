"""
RSI Divergence Trading Strategy
Identifies bullish and bearish divergences between price and RSI indicator
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from core.trade_executor import TradeSignal, TradeDirection

@dataclass
class DivergenceSignal:
    """Divergence signal data structure"""
    type: str  # 'bullish' or 'bearish'
    strength: float  # 0.0 to 1.0
    price_points: List[float]
    rsi_points: List[float]
    timeframe: str
    confidence: float

class RSIDivergenceStrategy:
    """RSI Divergence trading strategy implementation"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        self.rsi_period = self.config.get('rsi_period', 14)
        self.lookback_period = self.config.get('lookback_period', 50)
        self.min_divergence_strength = self.config.get('min_divergence_strength', 0.6)
        self.risk_reward_ratio = self.config.get('risk_reward_ratio', 2.0)
        
        self.rsi_overbought = self.config.get('rsi_overbought', 70)
        self.rsi_oversold = self.config.get('rsi_oversold', 30)
        
        self.min_peaks_distance = self.config.get('min_peaks_distance', 10)
        self.peak_prominence = self.config.get('peak_prominence', 2.0)
        
        self.name = "RSI_Divergence"
        self.timeframes = ["H1", "H4"]
        
    def analyze(self, df: pd.DataFrame, symbol: str = "EURUSD") -> Dict[str, Any]:
        """Analyze market data for RSI divergence signals"""
        try:
            if df is None or df.empty or len(df) < self.lookback_period:
                return {"signal": None, "analysis": "Insufficient data"}
            
            if 'rsi' not in df.columns:
                df = self._calculate_rsi(df)
            
            divergences = self._detect_divergences(df)
            
            signal = self._generate_signal(df, divergences, symbol)
            
            analysis = {
                "strategy": self.name,
                "symbol": symbol,
                "signal": signal,
                "divergences_found": len(divergences),
                "divergences": [self._divergence_to_dict(div) for div in divergences],
                "current_rsi": df['rsi'].iloc[-1] if 'rsi' in df.columns else None,
                "market_condition": self._assess_market_condition(df),
                "confidence": signal.confidence if signal else 0.0,
                "timestamp": datetime.now().isoformat()
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in RSI divergence analysis: {e}")
            return {"signal": None, "error": str(e)}
    
    def _calculate_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI indicator"""
        try:
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            return df
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {e}")
            return df
    
    def _detect_divergences(self, df: pd.DataFrame) -> List[DivergenceSignal]:
        """Detect bullish and bearish divergences"""
        divergences = []
        
        try:
            recent_df = df.tail(self.lookback_period).copy()
            
            if len(recent_df) < 20:
                return divergences
            
            price_peaks = self._find_peaks(recent_df['high'].values)
            price_troughs = self._find_troughs(recent_df['low'].values)
            
            rsi_peaks = self._find_peaks(recent_df['rsi'].values)
            rsi_troughs = self._find_troughs(recent_df['rsi'].values)
            
            bullish_div = self._check_bullish_divergence(
                recent_df, price_troughs, rsi_troughs
            )
            if bullish_div:
                divergences.append(bullish_div)
            
            bearish_div = self._check_bearish_divergence(
                recent_df, price_peaks, rsi_peaks
            )
            if bearish_div:
                divergences.append(bearish_div)
            
        except Exception as e:
            self.logger.error(f"Error detecting divergences: {e}")
        
        return divergences
    
    def _find_peaks(self, data) -> List[int]:
        """Find peaks in data"""
        peaks = []
        
        for i in range(self.min_peaks_distance, len(data) - self.min_peaks_distance):
            is_peak = True
            
            for j in range(i - self.min_peaks_distance, i + self.min_peaks_distance + 1):
                if j != i and data[j] >= data[i]:
                    is_peak = False
                    break
            
            if is_peak and data[i] > np.mean(data) + self.peak_prominence * np.std(data):
                peaks.append(i)
        
        return peaks
    
    def _find_troughs(self, data) -> List[int]:
        """Find troughs in data"""
        troughs = []
        
        for i in range(self.min_peaks_distance, len(data) - self.min_peaks_distance):
            is_trough = True
            
            for j in range(i - self.min_peaks_distance, i + self.min_peaks_distance + 1):
                if j != i and data[j] <= data[i]:
                    is_trough = False
                    break
            
            if is_trough and data[i] < np.mean(data) - self.peak_prominence * np.std(data):
                troughs.append(i)
        
        return troughs
    
    def _check_bullish_divergence(self, df: pd.DataFrame, price_troughs: List[int], 
                                 rsi_troughs: List[int]) -> Optional[DivergenceSignal]:
        """Check for bullish divergence"""
        if len(price_troughs) < 2 or len(rsi_troughs) < 2:
            return None
        
        try:
            last_price_troughs = sorted(price_troughs)[-2:]
            
            rsi_trough_1 = self._find_nearest_point(last_price_troughs[0], rsi_troughs)
            rsi_trough_2 = self._find_nearest_point(last_price_troughs[1], rsi_troughs)
            
            if rsi_trough_1 is None or rsi_trough_2 is None:
                return None
            
            price_1 = df['low'].iloc[last_price_troughs[0]]
            price_2 = df['low'].iloc[last_price_troughs[1]]
            rsi_1 = df['rsi'].iloc[rsi_trough_1]
            rsi_2 = df['rsi'].iloc[rsi_trough_2]
            
            if price_2 < price_1 and rsi_2 > rsi_1:
                strength = self._calculate_divergence_strength(
                    [price_1, price_2], [rsi_1, rsi_2], 'bullish'
                )
                
                if strength >= self.min_divergence_strength:
                    return DivergenceSignal(
                        type='bullish',
                        strength=strength,
                        price_points=[price_1, price_2],
                        rsi_points=[rsi_1, rsi_2],
                        timeframe='current',
                        confidence=min(0.9, strength + 0.1)
                    )
        
        except Exception as e:
            self.logger.error(f"Error checking bullish divergence: {e}")
        
        return None
    
    def _check_bearish_divergence(self, df: pd.DataFrame, price_peaks: List[int], 
                                 rsi_peaks: List[int]) -> Optional[DivergenceSignal]:
        """Check for bearish divergence"""
        if len(price_peaks) < 2 or len(rsi_peaks) < 2:
            return None
        
        try:
            last_price_peaks = sorted(price_peaks)[-2:]
            
            rsi_peak_1 = self._find_nearest_point(last_price_peaks[0], rsi_peaks)
            rsi_peak_2 = self._find_nearest_point(last_price_peaks[1], rsi_peaks)
            
            if rsi_peak_1 is None or rsi_peak_2 is None:
                return None
            
            price_1 = df['high'].iloc[last_price_peaks[0]]
            price_2 = df['high'].iloc[last_price_peaks[1]]
            rsi_1 = df['rsi'].iloc[rsi_peak_1]
            rsi_2 = df['rsi'].iloc[rsi_peak_2]
            
            if price_2 > price_1 and rsi_2 < rsi_1:
                strength = self._calculate_divergence_strength(
                    [price_1, price_2], [rsi_1, rsi_2], 'bearish'
                )
                
                if strength >= self.min_divergence_strength:
                    return DivergenceSignal(
                        type='bearish',
                        strength=strength,
                        price_points=[price_1, price_2],
                        rsi_points=[rsi_1, rsi_2],
                        timeframe='current',
                        confidence=min(0.9, strength + 0.1)
                    )
        
        except Exception as e:
            self.logger.error(f"Error checking bearish divergence: {e}")
        
        return None
    
    def _find_nearest_point(self, target_index: int, points: List[int]) -> Optional[int]:
        """Find nearest point in list to target index"""
        if not points:
            return None
        
        return min(points, key=lambda x: abs(x - target_index))
    
    def _calculate_divergence_strength(self, price_points: List[float], 
                                     rsi_points: List[float], div_type: str) -> float:
        """Calculate divergence strength"""
        try:
            price_change = abs(price_points[1] - price_points[0]) / price_points[0]
            rsi_change = abs(rsi_points[1] - rsi_points[0]) / 100.0
            
            strength = min(1.0, (price_change + rsi_change) * 2)
            
            if div_type == 'bullish' and min(rsi_points) < self.rsi_oversold:
                strength += 0.2
            elif div_type == 'bearish' and max(rsi_points) > self.rsi_overbought:
                strength += 0.2
            
            return min(1.0, strength)
            
        except Exception as e:
            self.logger.error(f"Error calculating divergence strength: {e}")
            return 0.5
    
    def _generate_signal(self, df: pd.DataFrame, divergences: List[DivergenceSignal], 
                        symbol: str) -> Optional[TradeSignal]:
        """Generate trading signal based on divergences"""
        if not divergences:
            return None
        
        try:
            strongest_div = max(divergences, key=lambda x: x.strength)
            
            current_price = df['close'].iloc[-1]
            current_rsi = df['rsi'].iloc[-1]
            
            if strongest_div.type == 'bullish' and current_rsi < 40:
                atr = df['atr'].iloc[-1] if 'atr' in df.columns else current_price * 0.001
                
                stop_loss = current_price - (atr * 2)
                take_profit = current_price + (atr * self.risk_reward_ratio * 2)
                
                return TradeSignal(
                    symbol=symbol,
                    direction=TradeDirection.BUY,
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    risk_percent=2.0,
                    strategy_name=self.name,
                    confidence=strongest_div.confidence,
                    metadata={
                        "divergence_type": strongest_div.type,
                        "divergence_strength": strongest_div.strength,
                        "rsi_level": current_rsi,
                        "signal_reason": "Bullish RSI divergence detected"
                    }
                )
            
            elif strongest_div.type == 'bearish' and current_rsi > 60:
                atr = df['atr'].iloc[-1] if 'atr' in df.columns else current_price * 0.001
                
                stop_loss = current_price + (atr * 2)
                take_profit = current_price - (atr * self.risk_reward_ratio * 2)
                
                return TradeSignal(
                    symbol=symbol,
                    direction=TradeDirection.SELL,
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    risk_percent=2.0,
                    strategy_name=self.name,
                    confidence=strongest_div.confidence,
                    metadata={
                        "divergence_type": strongest_div.type,
                        "divergence_strength": strongest_div.strength,
                        "rsi_level": current_rsi,
                        "signal_reason": "Bearish RSI divergence detected"
                    }
                )
        
        except Exception as e:
            self.logger.error(f"Error generating signal: {e}")
        
        return None
    
    def _assess_market_condition(self, df: pd.DataFrame) -> str:
        """Assess current market condition"""
        try:
            if 'rsi' not in df.columns:
                return "unknown"
            
            current_rsi = df['rsi'].iloc[-1]
            
            if current_rsi > self.rsi_overbought:
                return "overbought"
            elif current_rsi < self.rsi_oversold:
                return "oversold"
            elif 40 <= current_rsi <= 60:
                return "neutral"
            elif current_rsi > 60:
                return "bullish"
            else:
                return "bearish"
                
        except Exception as e:
            self.logger.error(f"Error assessing market condition: {e}")
            return "unknown"
    
    def _divergence_to_dict(self, divergence: DivergenceSignal) -> Dict:
        """Convert divergence signal to dictionary"""
        return {
            "type": divergence.type,
            "strength": divergence.strength,
            "price_points": divergence.price_points,
            "rsi_points": divergence.rsi_points,
            "timeframe": divergence.timeframe,
            "confidence": divergence.confidence
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "description": "RSI Divergence strategy identifies bullish and bearish divergences between price and RSI",
            "timeframes": self.timeframes,
            "parameters": {
                "rsi_period": self.rsi_period,
                "lookback_period": self.lookback_period,
                "min_divergence_strength": self.min_divergence_strength,
                "risk_reward_ratio": self.risk_reward_ratio,
                "rsi_overbought": self.rsi_overbought,
                "rsi_oversold": self.rsi_oversold
            },
            "risk_level": "medium",
            "suitable_for": ["trending", "ranging"],
            "market_conditions": ["normal", "volatile"]
        }
