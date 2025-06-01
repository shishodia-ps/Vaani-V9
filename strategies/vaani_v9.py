"""
VaaniV9 Strategy - The Ultimate Forex Trading Strategy
Exceptional strategy with adaptive risk management, capital preservation, and doomsday protection
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class MarketRegime:
    """Market regime classification"""
    regime_type: str
    volatility_level: float
    trend_strength: float
    risk_level: str
    confidence: float

@dataclass
class RiskMetrics:
    """Risk assessment metrics"""
    var_95: float
    max_drawdown: float
    sharpe_ratio: float
    correlation_risk: float
    tail_risk_score: float

class VaaniV9Strategy:
    """VaaniV9 - The ultimate adaptive forex trading strategy"""
    
    def __init__(self, 
                 base_risk_percent: float = 0.5,
                 max_risk_percent: float = 2.0,
                 doomsday_threshold: float = 0.05,
                 correlation_threshold: float = 0.8,
                 volatility_lookback: int = 100,
                 regime_detection_period: int = 50,
                 capital_preservation_mode: bool = True,
                 adaptive_position_sizing: bool = True,
                 multi_timeframe_analysis: bool = True):
        
        self.base_risk_percent = base_risk_percent
        self.max_risk_percent = max_risk_percent
        self.doomsday_threshold = doomsday_threshold
        self.correlation_threshold = correlation_threshold
        self.volatility_lookback = volatility_lookback
        self.regime_detection_period = regime_detection_period
        self.capital_preservation_mode = capital_preservation_mode
        self.adaptive_position_sizing = adaptive_position_sizing
        self.multi_timeframe_analysis = multi_timeframe_analysis
        
        self.logger = logging.getLogger(__name__)
        
        self.current_regime = None
        self.risk_metrics = None
        self.emergency_mode = False
        self.last_regime_update = None
        
        self.strategy_weights = {
            'trend_following': 0.3,
            'mean_reversion': 0.25,
            'momentum': 0.2,
            'volatility_breakout': 0.15,
            'correlation_hedge': 0.1
        }
        
    def analyze(self, data: pd.DataFrame, symbol: str = "EURUSD") -> Dict[str, Any]:
        """Analyze market with VaaniV9's advanced multi-strategy approach"""
        try:
            if len(data) < self.volatility_lookback:
                return self._no_signal_result("Insufficient data for VaaniV9 analysis")
            
            current_price = data['close'].iloc[-1]
            
            regime_analysis = self._detect_market_regime(data)
            self.current_regime = regime_analysis
            
            risk_assessment = self._comprehensive_risk_assessment(data)
            self.risk_metrics = risk_assessment
            
            if self._check_doomsday_conditions(data, risk_assessment):
                return self._doomsday_protection_mode(data)
            
            multi_strategy_signals = self._generate_multi_strategy_signals(data, regime_analysis)
            
            final_signal = self._adaptive_signal_fusion(multi_strategy_signals, regime_analysis, risk_assessment)
            
            position_sizing = self._calculate_adaptive_position_size(final_signal, risk_assessment, regime_analysis)
            
            return {
                'signal': final_signal['signal'],
                'confidence': final_signal['confidence'],
                'entry_price': current_price,
                'position_size': position_sizing['size'],
                'risk_adjusted_size': position_sizing['risk_adjusted'],
                'market_regime': regime_analysis.regime_type,
                'risk_level': 'HIGH' if risk_assessment.tail_risk_score > 0.1 else 'MEDIUM' if risk_assessment.var_95 < -0.02 else 'LOW',
                'doomsday_protection': self.emergency_mode,
                'strategy_blend': final_signal['strategy_composition'],
                'analysis': {
                    'strategy': 'VaaniV9',
                    'regime_confidence': regime_analysis.confidence,
                    'risk_score': abs(risk_assessment.var_95) + abs(risk_assessment.max_drawdown),
                    'volatility_regime': regime_analysis.volatility_level,
                    'trend_strength': regime_analysis.trend_strength,
                    'capital_protection_active': self.capital_preservation_mode,
                    'emergency_mode': self.emergency_mode,
                    'market_condition': self._assess_market_condition(data)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in VaaniV9 analysis: {e}")
            return self._emergency_safe_mode()
    
    def _detect_market_regime(self, data: pd.DataFrame) -> MarketRegime:
        """Detect current market regime using advanced analysis"""
        
        returns = data['close'].pct_change().dropna()
        
        short_vol = returns.tail(20).std()
        medium_vol = returns.tail(50).std()
        long_vol = returns.tail(self.volatility_lookback).std()
        
        volatility_level = short_vol / long_vol if long_vol > 0 else 1.0
        
        sma_20 = data['close'].rolling(20).mean()
        sma_50 = data['close'].rolling(50).mean()
        sma_100 = data['close'].rolling(100).mean()
        
        current_price = data['close'].iloc[-1]
        
        trend_score = 0.0
        if current_price > sma_20.iloc[-1] > sma_50.iloc[-1] > sma_100.iloc[-1]:
            trend_score = 1.0
        elif current_price < sma_20.iloc[-1] < sma_50.iloc[-1] < sma_100.iloc[-1]:
            trend_score = -1.0
        else:
            trend_score = 0.0
        
        trend_strength = abs(trend_score)
        
        adx = self._calculate_adx(data)
        rsi = self._calculate_rsi(data)
        
        if volatility_level > 2.0 and trend_strength < 0.3:
            regime_type = "CRISIS"
            risk_level = "EXTREME"
            confidence = 0.9
        elif volatility_level > 1.5:
            regime_type = "HIGH_VOLATILITY"
            risk_level = "HIGH"
            confidence = 0.8
        elif trend_strength > 0.7 and adx > 25:
            regime_type = "STRONG_TREND"
            risk_level = "MEDIUM"
            confidence = 0.8
        elif trend_strength < 0.3 and volatility_level < 0.8:
            regime_type = "RANGING"
            risk_level = "LOW"
            confidence = 0.7
        else:
            regime_type = "TRANSITIONAL"
            risk_level = "MEDIUM"
            confidence = 0.6
        
        return MarketRegime(
            regime_type=regime_type,
            volatility_level=volatility_level,
            trend_strength=trend_strength,
            risk_level=risk_level,
            confidence=confidence
        )
    
    def _comprehensive_risk_assessment(self, data: pd.DataFrame) -> RiskMetrics:
        """Comprehensive risk assessment with multiple metrics"""
        
        returns = data['close'].pct_change().dropna()
        
        var_95 = np.percentile(returns.tail(self.volatility_lookback), 5)
        
        cumulative_returns = (1 + returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        if len(returns) > 30:
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        else:
            sharpe_ratio = 0
        
        recent_returns = returns.tail(50)
        correlation_risk = self._calculate_correlation_risk(recent_returns)
        
        tail_events = (returns < var_95).sum()
        tail_risk_score = tail_events / len(returns) if len(returns) > 0 else 0
        
        risk_score = (
            abs(var_95) * 0.3 +
            abs(max_drawdown) * 0.3 +
            (1 - min(sharpe_ratio, 2) / 2) * 0.2 +
            correlation_risk * 0.1 +
            tail_risk_score * 0.1
        )
        
        if risk_score > 0.8:
            overall_risk = "EXTREME"
        elif risk_score > 0.6:
            overall_risk = "HIGH"
        elif risk_score > 0.4:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"
        
        return RiskMetrics(
            var_95=float(var_95),
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            correlation_risk=correlation_risk,
            tail_risk_score=tail_risk_score
        )
    
    def _check_doomsday_conditions(self, data: pd.DataFrame, risk_metrics: RiskMetrics) -> bool:
        """Check for doomsday market conditions"""
        
        returns = data['close'].pct_change().dropna()
        recent_returns = returns.tail(10)
        
        extreme_volatility = returns.tail(20).std() > self.doomsday_threshold
        
        consecutive_losses = (recent_returns < -0.01).sum() > 7
        
        flash_crash = any(recent_returns < -0.03)
        
        extreme_var = abs(risk_metrics.var_95) > self.doomsday_threshold
        
        correlation_breakdown = risk_metrics.correlation_risk > 0.9
        
        doomsday_detected = (
            extreme_volatility or
            consecutive_losses or
            flash_crash or
            extreme_var or
            correlation_breakdown
        )
        
        if doomsday_detected and not self.emergency_mode:
            self.logger.warning("DOOMSDAY CONDITIONS DETECTED - Activating emergency protection")
            self.emergency_mode = True
        elif not doomsday_detected and self.emergency_mode:
            self.logger.info("Market conditions stabilized - Deactivating emergency mode")
            self.emergency_mode = False
        
        return doomsday_detected
    
    def _doomsday_protection_mode(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Emergency doomsday protection mode"""
        
        current_price = data['close'].iloc[-1]
        
        return {
            'signal': 'EMERGENCY_HOLD',
            'confidence': 1.0,
            'entry_price': current_price,
            'position_size': 0.0,
            'risk_adjusted_size': 0.0,
            'emergency_mode': True,
            'protection_reason': 'Doomsday conditions detected',
            'analysis': {
                'strategy': 'VaaniV9',
                'mode': 'EMERGENCY_PROTECTION',
                'action': 'Capital preservation activated',
                'recommendation': 'Close all positions and wait for market stabilization'
            }
        }
    
    def _generate_multi_strategy_signals(self, data: pd.DataFrame, regime: MarketRegime) -> Dict[str, Any]:
        """Generate signals from multiple strategies"""
        
        signals = {}
        
        signals['trend_following'] = self._trend_following_signal(data, regime)
        signals['mean_reversion'] = self._mean_reversion_signal(data, regime)
        signals['momentum'] = self._momentum_signal(data, regime)
        signals['volatility_breakout'] = self._volatility_breakout_signal(data, regime)
        signals['correlation_hedge'] = self._correlation_hedge_signal(data, regime)
        
        return signals
    
    def _trend_following_signal(self, data: pd.DataFrame, regime: MarketRegime) -> Dict[str, Any]:
        """Advanced trend following signal"""
        
        if regime.regime_type not in ["STRONG_TREND", "TRANSITIONAL"]:
            return {'signal': 'HOLD', 'confidence': 0.0, 'strength': 0.0}
        
        ema_12 = data['close'].ewm(span=12).mean()
        ema_26 = data['close'].ewm(span=26).mean()
        ema_50 = data['close'].ewm(span=50).mean()
        
        current_price = data['close'].iloc[-1]
        
        if current_price > ema_12.iloc[-1] > ema_26.iloc[-1] > ema_50.iloc[-1]:
            signal = 'BUY'
            confidence = 0.8 * regime.confidence
            strength = regime.trend_strength
        elif current_price < ema_12.iloc[-1] < ema_26.iloc[-1] < ema_50.iloc[-1]:
            signal = 'SELL'
            confidence = 0.8 * regime.confidence
            strength = regime.trend_strength
        else:
            signal = 'HOLD'
            confidence = 0.0
            strength = 0.0
        
        return {'signal': signal, 'confidence': confidence, 'strength': strength}
    
    def _mean_reversion_signal(self, data: pd.DataFrame, regime: MarketRegime) -> Dict[str, Any]:
        """Mean reversion signal for ranging markets"""
        
        if regime.regime_type not in ["RANGING", "HIGH_VOLATILITY"]:
            return {'signal': 'HOLD', 'confidence': 0.0, 'strength': 0.0}
        
        rsi = self._calculate_rsi(data)
        bollinger_bands = self._calculate_bollinger_bands(data)
        
        current_price = data['close'].iloc[-1]
        current_rsi = rsi.iloc[-1]
        
        upper_band = bollinger_bands['upper'].iloc[-1]
        lower_band = bollinger_bands['lower'].iloc[-1]
        
        if current_rsi < 30 and current_price < lower_band:
            signal = 'BUY'
            confidence = 0.7
            strength = (30 - current_rsi) / 30
        elif current_rsi > 70 and current_price > upper_band:
            signal = 'SELL'
            confidence = 0.7
            strength = (current_rsi - 70) / 30
        else:
            signal = 'HOLD'
            confidence = 0.0
            strength = 0.0
        
        return {'signal': signal, 'confidence': confidence, 'strength': strength}
    
    def _momentum_signal(self, data: pd.DataFrame, regime: MarketRegime) -> Dict[str, Any]:
        """Momentum-based signal"""
        
        macd_line, macd_signal, macd_histogram = self._calculate_macd(data)
        
        current_macd = macd_line.iloc[-1]
        current_signal = macd_signal.iloc[-1]
        current_histogram = macd_histogram.iloc[-1]
        
        if current_macd > current_signal and current_histogram > 0:
            signal = 'BUY'
            confidence = 0.6
            strength = min(abs(current_histogram) * 1000, 1.0)
        elif current_macd < current_signal and current_histogram < 0:
            signal = 'SELL'
            confidence = 0.6
            strength = min(abs(current_histogram) * 1000, 1.0)
        else:
            signal = 'HOLD'
            confidence = 0.0
            strength = 0.0
        
        return {'signal': signal, 'confidence': confidence, 'strength': strength}
    
    def _volatility_breakout_signal(self, data: pd.DataFrame, regime: MarketRegime) -> Dict[str, Any]:
        """Volatility breakout signal"""
        
        if regime.volatility_level < 1.2:
            return {'signal': 'HOLD', 'confidence': 0.0, 'strength': 0.0}
        
        atr = self._calculate_atr(data)
        current_price = data['close'].iloc[-1]
        
        recent_high = data['high'].tail(20).max()
        recent_low = data['low'].tail(20).min()
        
        breakout_threshold = atr * 1.5
        
        if current_price > recent_high + breakout_threshold:
            signal = 'BUY'
            confidence = 0.7
            strength = regime.volatility_level / 3.0
        elif current_price < recent_low - breakout_threshold:
            signal = 'SELL'
            confidence = 0.7
            strength = regime.volatility_level / 3.0
        else:
            signal = 'HOLD'
            confidence = 0.0
            strength = 0.0
        
        return {'signal': signal, 'confidence': confidence, 'strength': strength}
    
    def _correlation_hedge_signal(self, data: pd.DataFrame, regime: MarketRegime) -> Dict[str, Any]:
        """Correlation-based hedging signal"""
        
        if regime.regime_type != "CRISIS":
            return {'signal': 'HOLD', 'confidence': 0.0, 'strength': 0.0}
        
        returns = data['close'].pct_change().dropna()
        recent_correlation = self._calculate_correlation_risk(returns.tail(30))
        
        if recent_correlation > self.correlation_threshold:
            signal = 'HEDGE'
            confidence = 0.8
            strength = recent_correlation
        else:
            signal = 'HOLD'
            confidence = 0.0
            strength = 0.0
        
        return {'signal': signal, 'confidence': confidence, 'strength': strength}
    
    def _adaptive_signal_fusion(self, signals: Dict, regime: MarketRegime, risk_metrics: RiskMetrics) -> Dict[str, Any]:
        """Fuse multiple strategy signals adaptively"""
        
        if self.emergency_mode:
            return {'signal': 'HOLD', 'confidence': 1.0, 'strategy_composition': 'Emergency mode'}
        
        weighted_signals = {}
        total_weight = 0.0
        
        for strategy, signal_data in signals.items():
            if signal_data['signal'] != 'HOLD':
                weight = self.strategy_weights[strategy] * signal_data['confidence'] * signal_data['strength']
                weighted_signals[strategy] = {
                    'signal': signal_data['signal'],
                    'weight': weight
                }
                total_weight += weight
        
        if total_weight == 0:
            return {'signal': 'HOLD', 'confidence': 0.0, 'strategy_composition': 'No strong signals'}
        
        buy_weight = sum(data['weight'] for data in weighted_signals.values() if data['signal'] == 'BUY')
        sell_weight = sum(data['weight'] for data in weighted_signals.values() if data['signal'] == 'SELL')
        hedge_weight = sum(data['weight'] for data in weighted_signals.values() if data['signal'] == 'HEDGE')
        
        if hedge_weight > buy_weight and hedge_weight > sell_weight:
            final_signal = 'HEDGE'
            confidence = hedge_weight / total_weight
        elif buy_weight > sell_weight:
            final_signal = 'BUY'
            confidence = buy_weight / total_weight
        elif sell_weight > buy_weight:
            final_signal = 'SELL'
            confidence = sell_weight / total_weight
        else:
            final_signal = 'HOLD'
            confidence = 0.0
        
        risk_adjustment = 1.0 - min(abs(risk_metrics.var_95) * 10, 0.5)
        confidence *= risk_adjustment
        
        strategy_composition = {k: v['weight']/total_weight for k, v in weighted_signals.items()}
        
        return {
            'signal': final_signal,
            'confidence': min(confidence, 0.95),
            'strategy_composition': strategy_composition
        }
    
    def _calculate_adaptive_position_size(self, signal: Dict, risk_metrics: RiskMetrics, regime: MarketRegime) -> Dict[str, Any]:
        """Calculate adaptive position size based on risk and market conditions"""
        
        if signal['signal'] in ['HOLD', 'EMERGENCY_HOLD']:
            return {'size': 0.0, 'risk_adjusted': 0.0}
        
        base_size = self.base_risk_percent
        
        confidence_multiplier = signal['confidence']
        
        if regime.risk_level == "LOW":
            regime_multiplier = 1.5
        elif regime.risk_level == "MEDIUM":
            regime_multiplier = 1.0
        elif regime.risk_level == "HIGH":
            regime_multiplier = 0.5
        else:
            regime_multiplier = 0.2
        
        volatility_adjustment = 1.0 / max(regime.volatility_level, 0.5)
        
        sharpe_adjustment = min(max(risk_metrics.sharpe_ratio, 0), 2) / 2
        
        var_adjustment = 1.0 - min(abs(risk_metrics.var_95) * 20, 0.8)
        
        final_size = (base_size * 
                     confidence_multiplier * 
                     regime_multiplier * 
                     volatility_adjustment * 
                     (0.5 + 0.5 * sharpe_adjustment) * 
                     var_adjustment)
        
        final_size = max(0.1, min(final_size, self.max_risk_percent))
        
        return {
            'size': final_size,
            'risk_adjusted': final_size,
            'components': {
                'base': base_size,
                'confidence': confidence_multiplier,
                'regime': regime_multiplier,
                'volatility': volatility_adjustment,
                'sharpe': sharpe_adjustment,
                'var': var_adjustment
            }
        }
    
    def _calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_adx(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average Directional Index"""
        high = data['high']
        low = data['low']
        close = data['close']
        
        plus_dm = high.diff()
        minus_dm = low.diff()
        plus_dm = plus_dm.where(plus_dm > 0, 0)
        minus_dm = minus_dm.where(minus_dm < 0, 0)
        
        tr1 = pd.DataFrame(high - low)
        tr2 = pd.DataFrame(abs(high - close.shift(1)))
        tr3 = pd.DataFrame(abs(low - close.shift(1)))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(period).mean()
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.abs().rolling(period).mean() / atr)
        
        dx = (abs(plus_di - minus_di) / abs(plus_di + minus_di)) * 100
        adx = dx.rolling(period).mean()
        
        return adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 20
    
    def _calculate_bollinger_bands(self, data: pd.DataFrame, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = data['close'].rolling(period).mean()
        std = data['close'].rolling(period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }
    
    def _calculate_macd(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD indicator"""
        ema_12 = data['close'].ewm(span=12).mean()
        ema_26 = data['close'].ewm(span=26).mean()
        macd_line = ema_12 - ema_26
        macd_signal = macd_line.ewm(span=9).mean()
        macd_histogram = macd_line - macd_signal
        
        return macd_line, macd_signal, macd_histogram
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift())
        low_close = abs(data['low'] - data['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean().iloc[-1]
        
        return atr if not pd.isna(atr) else 0.001
    
    def _calculate_correlation_risk(self, returns: pd.Series) -> float:
        """Calculate correlation risk metric"""
        if len(returns) < 10:
            return 0.0
        
        rolling_corr = returns.rolling(10).corr(returns.shift(1))
        avg_correlation = rolling_corr.mean()
        
        return abs(avg_correlation) if not pd.isna(avg_correlation) else 0.0
    
    def _assess_market_condition(self, data: pd.DataFrame) -> str:
        """Assess current market condition with VaaniV9's advanced analysis"""
        if self.emergency_mode:
            return "EMERGENCY MODE - Capital protection active"
        
        if self.current_regime:
            regime = self.current_regime.regime_type
            risk = self.current_regime.risk_level
            
            return f"{regime} regime with {risk} risk - VaaniV9 adaptive mode"
        
        return "VaaniV9 analyzing market conditions"
    
    def _emergency_safe_mode(self) -> Dict[str, Any]:
        """Emergency safe mode when analysis fails"""
        return {
            'signal': 'EMERGENCY_HOLD',
            'confidence': 1.0,
            'entry_price': 0.0,
            'position_size': 0.0,
            'emergency_mode': True,
            'analysis': {
                'strategy': 'VaaniV9',
                'mode': 'EMERGENCY_SAFE_MODE',
                'reason': 'Analysis error - protecting capital'
            }
        }
    
    def _no_signal_result(self, reason: str) -> Dict[str, Any]:
        """Return no signal result"""
        return {
            'signal': 'HOLD',
            'confidence': 0.0,
            'entry_price': 0.0,
            'reason': reason,
            'analysis': {
                'strategy': 'VaaniV9',
                'status': 'No signal',
                'reason': reason
            }
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get VaaniV9 strategy information"""
        return {
            'name': 'VaaniV9 - Ultimate Forex Strategy',
            'description': 'Advanced adaptive strategy with capital preservation and doomsday protection',
            'version': '9.0',
            'parameters': {
                'base_risk_percent': self.base_risk_percent,
                'max_risk_percent': self.max_risk_percent,
                'doomsday_threshold': self.doomsday_threshold,
                'correlation_threshold': self.correlation_threshold,
                'volatility_lookback': self.volatility_lookback,
                'regime_detection_period': self.regime_detection_period,
                'capital_preservation_mode': self.capital_preservation_mode,
                'adaptive_position_sizing': self.adaptive_position_sizing,
                'multi_timeframe_analysis': self.multi_timeframe_analysis
            },
            'features': [
                'Adaptive market regime detection',
                'Multi-strategy signal fusion',
                'Dynamic position sizing',
                'Comprehensive risk assessment',
                'Doomsday protection protocols',
                'Capital preservation mechanisms',
                'Correlation-based hedging',
                'Emergency safe mode'
            ],
            'market_conditions': 'Adapts to all market conditions with regime-specific strategies',
            'risk_level': 'Adaptive (Low to Medium based on conditions)',
            'timeframe': 'Multi-timeframe (M15-D1)',
            'suitable_for': [
                'all_market_conditions',
                'capital_preservation',
                'risk_management',
                'adaptive_trading',
                'crisis_protection'
            ],
            'protection_mechanisms': [
                'VaR-based risk limits',
                'Drawdown protection',
                'Volatility spike detection',
                'Correlation breakdown alerts',
                'Emergency position closure',
                'Capital preservation mode'
            ],
            'strategy_components': {
                'trend_following': 'EMA-based trend detection with ADX confirmation',
                'mean_reversion': 'RSI and Bollinger Band reversals',
                'momentum': 'MACD-based momentum signals',
                'volatility_breakout': 'ATR-based breakout detection',
                'correlation_hedge': 'Crisis correlation hedging'
            },
            'warnings': [
                'Requires sufficient historical data',
                'Emergency mode may halt trading during extreme conditions',
                'Performance depends on accurate regime detection'
            ]
        }
