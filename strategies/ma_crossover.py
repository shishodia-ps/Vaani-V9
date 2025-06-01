"""
Moving Average Crossover Strategy
Classic trend-following strategy using multiple moving averages
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from core.trade_executor import TradeSignal, TradeDirection

class MAType(Enum):
    SMA = "sma"
    EMA = "ema"
    WMA = "wma"

class TrendStrength(Enum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"

class MACrossoverStrategy:
    """Moving Average Crossover trading strategy"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        self.fast_period = self.config.get('fast_period', 20)
        self.slow_period = self.config.get('slow_period', 50)
        self.signal_period = self.config.get('signal_period', 200)
        self.ma_type = MAType(self.config.get('ma_type', 'ema'))
        
        self.risk_reward_ratio = self.config.get('risk_reward_ratio', 2.0)
        self.atr_multiplier = self.config.get('atr_multiplier', 2.0)
        self.max_risk_percent = self.config.get('max_risk_percent', 2.0)
        
        self.require_trend_confirmation = self.config.get('require_trend_confirmation', True)
        self.min_trend_strength = self.config.get('min_trend_strength', 0.6)
        
        self.name = "MA_Crossover"
        self.timeframes = ["H1", "H4", "D1"]
        
    def analyze(self, df: pd.DataFrame, symbol: str = "EURUSD") -> Dict[str, Any]:
        """Analyze market data for MA crossover signals"""
        try:
            if df is None or df.empty or len(df) < self.signal_period:
                return {"signal": None, "analysis": "Insufficient data"}
            
            df = self._calculate_moving_averages(df)
            
            crossover_signal = self._detect_crossover(df)
            
            trend_analysis = self._analyze_trend(df)
            
            signal = self._generate_signal(df, crossover_signal, trend_analysis, symbol)
            
            analysis = {
                "strategy": self.name,
                "symbol": symbol,
                "signal": signal,
                "crossover_signal": crossover_signal,
                "trend_analysis": trend_analysis,
                "ma_values": self._get_current_ma_values(df),
                "market_condition": self._assess_market_condition(df),
                "confidence": signal.confidence if signal else 0.0,
                "timestamp": datetime.now().isoformat()
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in MA crossover analysis: {e}")
            return {"signal": None, "error": str(e)}
    
    def _calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate moving averages based on type"""
        try:
            if self.ma_type == MAType.SMA:
                df[f'ma_fast'] = df['close'].rolling(window=self.fast_period).mean()
                df[f'ma_slow'] = df['close'].rolling(window=self.slow_period).mean()
                df[f'ma_signal'] = df['close'].rolling(window=self.signal_period).mean()
            
            elif self.ma_type == MAType.EMA:
                df[f'ma_fast'] = df['close'].ewm(span=self.fast_period).mean()
                df[f'ma_slow'] = df['close'].ewm(span=self.slow_period).mean()
                df[f'ma_signal'] = df['close'].ewm(span=self.signal_period).mean()
            
            elif self.ma_type == MAType.WMA:
                weights_fast = np.arange(1, self.fast_period + 1)
                weights_slow = np.arange(1, self.slow_period + 1)
                weights_signal = np.arange(1, self.signal_period + 1)
                
                df[f'ma_fast'] = df['close'].rolling(window=self.fast_period).apply(
                    lambda x: np.average(x, weights=weights_fast), raw=True
                )
                df[f'ma_slow'] = df['close'].rolling(window=self.slow_period).apply(
                    lambda x: np.average(x, weights=weights_slow), raw=True
                )
                df[f'ma_signal'] = df['close'].rolling(window=self.signal_period).apply(
                    lambda x: np.average(x, weights=weights_signal), raw=True
                )
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error calculating moving averages: {e}")
            return df
    
    def _detect_crossover(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect MA crossover signals"""
        try:
            if len(df) < 2:
                return {"type": "none", "strength": 0.0}
            
            current_fast = df['ma_fast'].iloc[-1]
            current_slow = df['ma_slow'].iloc[-1]
            prev_fast = df['ma_fast'].iloc[-2]
            prev_slow = df['ma_slow'].iloc[-2]
            
            bullish_crossover = (prev_fast <= prev_slow) and (current_fast > current_slow)
            bearish_crossover = (prev_fast >= prev_slow) and (current_fast < current_slow)
            
            if bullish_crossover:
                strength = self._calculate_crossover_strength(df, "bullish")
                return {
                    "type": "bullish",
                    "strength": strength,
                    "fast_ma": current_fast,
                    "slow_ma": current_slow,
                    "crossover_point": len(df) - 1
                }
            
            elif bearish_crossover:
                strength = self._calculate_crossover_strength(df, "bearish")
                return {
                    "type": "bearish",
                    "strength": strength,
                    "fast_ma": current_fast,
                    "slow_ma": current_slow,
                    "crossover_point": len(df) - 1
                }
            
            else:
                if current_fast > current_slow:
                    alignment = "bullish_aligned"
                elif current_fast < current_slow:
                    alignment = "bearish_aligned"
                else:
                    alignment = "neutral"
                
                return {
                    "type": alignment,
                    "strength": 0.0,
                    "fast_ma": current_fast,
                    "slow_ma": current_slow
                }
                
        except Exception as e:
            self.logger.error(f"Error detecting crossover: {e}")
            return {"type": "none", "strength": 0.0}
    
    def _calculate_crossover_strength(self, df: pd.DataFrame, crossover_type: str) -> float:
        """Calculate the strength of the crossover signal"""
        try:
            recent_fast = df['ma_fast'].tail(5)
            recent_slow = df['ma_slow'].tail(5)
            
            fast_slope = (recent_fast.iloc[-1] - recent_fast.iloc[0]) / len(recent_fast)
            slow_slope = (recent_slow.iloc[-1] - recent_slow.iloc[0]) / len(recent_slow)
            
            ma_separation = abs(recent_fast.iloc[-1] - recent_slow.iloc[-1])
            price_range = df['close'].tail(20).max() - df['close'].tail(20).min()
            separation_ratio = ma_separation / price_range if price_range > 0 else 0
            
            volume_confirmation = 1.0
            if 'volume' in df.columns:
                recent_volume = df['volume'].tail(5).mean()
                avg_volume = df['volume'].tail(20).mean()
                volume_confirmation = min(2.0, recent_volume / avg_volume) if avg_volume > 0 else 1.0
            
            slope_factor = min(1.0, abs(fast_slope - slow_slope) * 1000)
            separation_factor = min(1.0, separation_ratio * 10)
            
            strength = (slope_factor * 0.4 + separation_factor * 0.4 + 
                       (volume_confirmation - 1.0) * 0.2)
            
            return max(0.0, min(1.0, strength))
            
        except Exception as e:
            self.logger.error(f"Error calculating crossover strength: {e}")
            return 0.5
    
    def _analyze_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze overall trend using multiple timeframes"""
        try:
            current_price = df['close'].iloc[-1]
            ma_fast = df['ma_fast'].iloc[-1]
            ma_slow = df['ma_slow'].iloc[-1]
            ma_signal = df['ma_signal'].iloc[-1]
            
            if current_price > ma_fast > ma_slow > ma_signal:
                trend_direction = "strong_uptrend"
                trend_strength = TrendStrength.STRONG
            elif current_price > ma_fast > ma_slow:
                trend_direction = "uptrend"
                trend_strength = TrendStrength.MODERATE
            elif current_price > ma_fast:
                trend_direction = "weak_uptrend"
                trend_strength = TrendStrength.WEAK
            elif current_price < ma_fast < ma_slow < ma_signal:
                trend_direction = "strong_downtrend"
                trend_strength = TrendStrength.STRONG
            elif current_price < ma_fast < ma_slow:
                trend_direction = "downtrend"
                trend_strength = TrendStrength.MODERATE
            elif current_price < ma_fast:
                trend_direction = "weak_downtrend"
                trend_strength = TrendStrength.WEAK
            else:
                trend_direction = "sideways"
                trend_strength = TrendStrength.WEAK
            
            ma_distances = [
                abs(current_price - ma_fast),
                abs(ma_fast - ma_slow),
                abs(ma_slow - ma_signal)
            ]
            avg_distance = np.mean(ma_distances)
            price_range = df['close'].tail(50).max() - df['close'].tail(50).min()
            trend_score = min(1.0, avg_distance / price_range) if price_range > 0 else 0
            
            ma_fast_slope = self._calculate_ma_slope(df['ma_fast'].tail(10))
            ma_slow_slope = self._calculate_ma_slope(df['ma_slow'].tail(10))
            
            slope_consistency = 1.0 - abs(ma_fast_slope - ma_slow_slope) / max(abs(ma_fast_slope), abs(ma_slow_slope), 1e-6)
            
            return {
                "direction": trend_direction,
                "strength": trend_strength.value,
                "score": trend_score,
                "consistency": slope_consistency,
                "ma_alignment": self._check_ma_alignment(current_price, ma_fast, ma_slow, ma_signal),
                "fast_slope": ma_fast_slope,
                "slow_slope": ma_slow_slope
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing trend: {e}")
            return {
                "direction": "unknown",
                "strength": "weak",
                "score": 0.0,
                "consistency": 0.0
            }
    
    def _calculate_ma_slope(self, ma_series: pd.Series) -> float:
        """Calculate the slope of a moving average"""
        try:
            if len(ma_series) < 2:
                return 0.0
            
            x = np.arange(len(ma_series))
            y = ma_series.values
            
            slope = np.polyfit(x, y.astype(float), 1)[0]
            return slope
            
        except Exception as e:
            self.logger.error(f"Error calculating MA slope: {e}")
            return 0.0
    
    def _check_ma_alignment(self, price: float, fast: float, slow: float, signal: float) -> str:
        """Check moving average alignment"""
        if price > fast > slow > signal:
            return "bullish_perfect"
        elif price < fast < slow < signal:
            return "bearish_perfect"
        elif price > fast > slow:
            return "bullish_partial"
        elif price < fast < slow:
            return "bearish_partial"
        else:
            return "mixed"
    
    def _generate_signal(self, df: pd.DataFrame, crossover_signal: Dict, 
                        trend_analysis: Dict, symbol: str) -> Optional[TradeSignal]:
        """Generate trading signal based on crossover and trend analysis"""
        try:
            if crossover_signal["type"] not in ["bullish", "bearish"]:
                return None
            
            if self.require_trend_confirmation:
                if trend_analysis["score"] < self.min_trend_strength:
                    return None
            
            current_price = df['close'].iloc[-1]
            
            atr = df['atr'].iloc[-1] if 'atr' in df.columns else current_price * 0.001
            
            if crossover_signal["type"] == "bullish":
                stop_loss = current_price - (atr * self.atr_multiplier)
                take_profit = current_price + (atr * self.atr_multiplier * self.risk_reward_ratio)
                
                ma_slow = crossover_signal["slow_ma"]
                stop_loss = max(stop_loss, ma_slow * 0.999)  # Don't go too far below slow MA
                
                confidence = min(0.9, crossover_signal["strength"] + trend_analysis["score"] * 0.3)
                
                return TradeSignal(
                    symbol=symbol,
                    direction=TradeDirection.BUY,
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    risk_percent=self.max_risk_percent,
                    strategy_name=self.name,
                    confidence=confidence,
                    metadata={
                        "crossover_strength": crossover_signal["strength"],
                        "trend_direction": trend_analysis["direction"],
                        "trend_score": trend_analysis["score"],
                        "ma_alignment": trend_analysis["ma_alignment"],
                        "signal_reason": f"Bullish MA crossover with {trend_analysis['strength']} trend"
                    }
                )
            
            elif crossover_signal["type"] == "bearish":
                stop_loss = current_price + (atr * self.atr_multiplier)
                take_profit = current_price - (atr * self.atr_multiplier * self.risk_reward_ratio)
                
                ma_slow = crossover_signal["slow_ma"]
                stop_loss = min(stop_loss, ma_slow * 1.001)  # Don't go too far above slow MA
                
                confidence = min(0.9, crossover_signal["strength"] + trend_analysis["score"] * 0.3)
                
                return TradeSignal(
                    symbol=symbol,
                    direction=TradeDirection.SELL,
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    risk_percent=self.max_risk_percent,
                    strategy_name=self.name,
                    confidence=confidence,
                    metadata={
                        "crossover_strength": crossover_signal["strength"],
                        "trend_direction": trend_analysis["direction"],
                        "trend_score": trend_analysis["score"],
                        "ma_alignment": trend_analysis["ma_alignment"],
                        "signal_reason": f"Bearish MA crossover with {trend_analysis['strength']} trend"
                    }
                )
        
        except Exception as e:
            self.logger.error(f"Error generating signal: {e}")
        
        return None
    
    def _get_current_ma_values(self, df: pd.DataFrame) -> Dict[str, float]:
        """Get current moving average values"""
        try:
            return {
                "fast_ma": df['ma_fast'].iloc[-1],
                "slow_ma": df['ma_slow'].iloc[-1],
                "signal_ma": df['ma_signal'].iloc[-1],
                "current_price": df['close'].iloc[-1]
            }
        except Exception as e:
            self.logger.error(f"Error getting MA values: {e}")
            return {}
    
    def _assess_market_condition(self, df: pd.DataFrame) -> str:
        """Assess current market condition"""
        try:
            trend_analysis = self._analyze_trend(df)
            
            if trend_analysis["strength"] == "strong":
                return f"strong_trend_{trend_analysis['direction'].split('_')[0]}"
            elif trend_analysis["strength"] == "moderate":
                return f"moderate_trend_{trend_analysis['direction'].split('_')[0]}"
            else:
                return "ranging"
                
        except Exception as e:
            self.logger.error(f"Error assessing market condition: {e}")
            return "unknown"
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "description": "Moving Average Crossover strategy using fast and slow MAs for trend following",
            "timeframes": self.timeframes,
            "parameters": {
                "fast_period": self.fast_period,
                "slow_period": self.slow_period,
                "signal_period": self.signal_period,
                "ma_type": self.ma_type.value,
                "risk_reward_ratio": self.risk_reward_ratio,
                "atr_multiplier": self.atr_multiplier
            },
            "risk_level": "medium",
            "suitable_for": ["trending"],
            "market_conditions": ["normal", "trending"]
        }
