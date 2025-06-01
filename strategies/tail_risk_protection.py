"""
Tail Risk Protection Strategy
Strategy focused on protecting against extreme market moves
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime

class TailRiskProtectionStrategy:
    """Tail risk protection strategy implementation"""
    
    def __init__(self, 
                 var_confidence: float = 0.05,
                 lookback_period: int = 252,
                 correlation_threshold: float = 0.7,
                 volatility_spike_threshold: float = 2.0,
                 max_portfolio_risk: float = 0.02,
                 hedge_activation_threshold: float = 0.015,
                 stop_loss_pips: float = 50.0,
                 take_profit_pips: float = 25.0):
        
        self.var_confidence = var_confidence
        self.lookback_period = lookback_period
        self.correlation_threshold = correlation_threshold
        self.volatility_spike_threshold = volatility_spike_threshold
        self.max_portfolio_risk = max_portfolio_risk
        self.hedge_activation_threshold = hedge_activation_threshold
        self.stop_loss_pips = stop_loss_pips
        self.take_profit_pips = take_profit_pips
        
        self.logger = logging.getLogger(__name__)
        
    def analyze(self, data: pd.DataFrame, symbol: str = "EURUSD") -> Dict[str, Any]:
        """Analyze market for tail risk protection opportunities"""
        try:
            if len(data) < self.lookback_period:
                return self._no_signal_result("Insufficient data for tail risk analysis")
            
            current_price = data['close'].iloc[-1]
            
            var_analysis = self._calculate_var(data)
            volatility_analysis = self._analyze_volatility_regime(data)
            correlation_analysis = self._analyze_correlation_breakdown(data)
            
            tail_risk_signal = self._evaluate_tail_risk(data, var_analysis, volatility_analysis, correlation_analysis)
            
            hedge_recommendation = self._recommend_hedge_strategy(tail_risk_signal)
            
            return {
                'signal': tail_risk_signal['signal'],
                'confidence': tail_risk_signal['confidence'],
                'entry_price': current_price,
                'var_estimate': var_analysis['var_estimate'],
                'volatility_regime': volatility_analysis['regime'],
                'correlation_stress': correlation_analysis['stress_level'],
                'hedge_type': hedge_recommendation['type'],
                'analysis': {
                    'strategy': 'Tail Risk Protection',
                    'risk_level': tail_risk_signal['risk_level'],
                    'protection_needed': tail_risk_signal['protection_needed'],
                    'market_stress': self._assess_market_stress(data),
                    'market_condition': self._assess_market_condition(data)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in tail risk analysis: {e}")
            return self._no_signal_result(f"Analysis error: {e}")
    
    def _calculate_var(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate Value at Risk"""
        
        returns = data['close'].pct_change().dropna()
        
        if len(returns) < self.lookback_period:
            lookback_data = returns
        else:
            lookback_data = returns.tail(self.lookback_period)
        
        var_estimate = np.percentile(lookback_data, self.var_confidence * 100)
        
        recent_returns = returns.tail(20)
        current_volatility = recent_returns.std()
        historical_volatility = lookback_data.std()
        
        volatility_ratio = current_volatility / historical_volatility if historical_volatility > 0 else 1.0
        
        adjusted_var = var_estimate * volatility_ratio
        
        return {
            'var_estimate': var_estimate,
            'adjusted_var': adjusted_var,
            'volatility_ratio': volatility_ratio,
            'current_volatility': current_volatility
        }
    
    def _analyze_volatility_regime(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze current volatility regime"""
        
        returns = data['close'].pct_change().dropna()
        
        short_vol = returns.tail(20).std()
        medium_vol = returns.tail(60).std()
        long_vol = returns.tail(self.lookback_period).std()
        
        vol_spike = short_vol / long_vol if long_vol > 0 else 1.0
        
        if vol_spike > self.volatility_spike_threshold:
            regime = 'HIGH_VOLATILITY'
            stress_level = min(vol_spike / self.volatility_spike_threshold, 3.0)
        elif vol_spike < 0.5:
            regime = 'LOW_VOLATILITY'
            stress_level = 0.2
        else:
            regime = 'NORMAL_VOLATILITY'
            stress_level = 0.5
        
        return {
            'regime': regime,
            'vol_spike_ratio': vol_spike,
            'stress_level': stress_level,
            'short_vol': short_vol,
            'long_vol': long_vol
        }
    
    def _analyze_correlation_breakdown(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze correlation breakdown patterns"""
        
        returns = data['close'].pct_change().dropna()
        
        if len(returns) < 60:
            return {'stress_level': 0.0, 'breakdown_detected': False}
        
        recent_returns = returns.tail(20)
        historical_returns = returns.tail(60)
        
        recent_extreme_moves = (abs(recent_returns) > recent_returns.std() * 2).sum()
        historical_extreme_moves = (abs(historical_returns) > historical_returns.std() * 2).sum()
        
        extreme_move_ratio = recent_extreme_moves / max(historical_extreme_moves, 1)
        
        breakdown_detected = extreme_move_ratio > 2.0
        stress_level = min(extreme_move_ratio, 3.0) / 3.0
        
        return {
            'stress_level': stress_level,
            'breakdown_detected': breakdown_detected,
            'extreme_move_ratio': extreme_move_ratio
        }
    
    def _evaluate_tail_risk(self, data: pd.DataFrame, var_info: Dict, vol_info: Dict, corr_info: Dict) -> Dict[str, Any]:
        """Evaluate overall tail risk"""
        
        risk_score = 0.0
        
        if vol_info['regime'] == 'HIGH_VOLATILITY':
            risk_score += 0.4
        elif vol_info['regime'] == 'LOW_VOLATILITY':
            risk_score += 0.1
        else:
            risk_score += 0.2
        
        risk_score += corr_info['stress_level'] * 0.3
        
        if var_info['volatility_ratio'] > 1.5:
            risk_score += 0.3
        
        if risk_score > 0.7:
            risk_level = 'HIGH'
            protection_needed = True
            signal = 'HEDGE'
            confidence = 0.8
        elif risk_score > 0.4:
            risk_level = 'MEDIUM'
            protection_needed = True
            signal = 'REDUCE_RISK'
            confidence = 0.6
        else:
            risk_level = 'LOW'
            protection_needed = False
            signal = 'HOLD'
            confidence = 0.3
        
        return {
            'signal': signal,
            'confidence': confidence,
            'risk_level': risk_level,
            'risk_score': risk_score,
            'protection_needed': protection_needed
        }
    
    def _recommend_hedge_strategy(self, tail_risk_info: Dict) -> Dict[str, Any]:
        """Recommend hedge strategy based on tail risk"""
        
        if not tail_risk_info['protection_needed']:
            return {'type': 'NONE', 'description': 'No hedging required'}
        
        if tail_risk_info['risk_level'] == 'HIGH':
            return {
                'type': 'PROTECTIVE_PUT',
                'description': 'Buy protective options or reduce position size significantly',
                'action': 'Immediate risk reduction'
            }
        elif tail_risk_info['risk_level'] == 'MEDIUM':
            return {
                'type': 'POSITION_SIZING',
                'description': 'Reduce position sizes and increase cash allocation',
                'action': 'Moderate risk reduction'
            }
        else:
            return {
                'type': 'MONITORING',
                'description': 'Increase monitoring frequency',
                'action': 'Enhanced surveillance'
            }
    
    def _assess_market_stress(self, data: pd.DataFrame) -> str:
        """Assess overall market stress level"""
        
        returns = data['close'].pct_change().dropna()
        
        if len(returns) < 20:
            return "Insufficient data"
        
        recent_volatility = returns.tail(20).std()
        
        negative_returns = (returns.tail(20) < 0).sum()
        large_moves = (abs(returns.tail(20)) > returns.std() * 2).sum()
        
        if recent_volatility > 0.02 and large_moves > 3:
            return "High stress - Extreme volatility"
        elif recent_volatility > 0.015 or large_moves > 2:
            return "Moderate stress - Elevated volatility"
        elif negative_returns > 15:
            return "Bearish stress - Persistent selling"
        else:
            return "Low stress - Normal conditions"
    
    def _assess_market_condition(self, data: pd.DataFrame) -> str:
        """Assess current market condition"""
        if len(data) < 50:
            return "Insufficient data"
        
        returns = data['close'].pct_change().dropna()
        volatility = returns.tail(20).std()
        
        if volatility > 0.02:
            return "Crisis mode - Maximum protection needed"
        elif volatility > 0.015:
            return "Stressed conditions - Hedging recommended"
        else:
            return "Normal conditions - Standard risk management"
    
    def _no_signal_result(self, reason: str) -> Dict[str, Any]:
        """Return no signal result"""
        return {
            'signal': 'HOLD',
            'confidence': 0.0,
            'entry_price': 0.0,
            'reason': reason,
            'analysis': {
                'strategy': 'Tail Risk Protection',
                'status': 'No signal',
                'reason': reason
            }
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': 'Tail Risk Protection Strategy',
            'description': 'Protects against extreme market moves and tail events',
            'parameters': {
                'var_confidence': self.var_confidence,
                'lookback_period': self.lookback_period,
                'correlation_threshold': self.correlation_threshold,
                'volatility_spike_threshold': self.volatility_spike_threshold,
                'max_portfolio_risk': self.max_portfolio_risk,
                'hedge_activation_threshold': self.hedge_activation_threshold,
                'stop_loss_pips': self.stop_loss_pips,
                'take_profit_pips': self.take_profit_pips
            },
            'market_conditions': 'Active during all market conditions with focus on stress periods',
            'risk_level': 'Low (Protective)',
            'timeframe': 'H1-D1',
            'suitable_for': ['risk_management', 'portfolio_protection'],
            'protection_types': ['VaR monitoring', 'Volatility regime detection', 'Correlation breakdown']
        }
