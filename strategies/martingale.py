"""
Martingale Trading Strategy
Doubles position size after each loss to recover losses with one winning trade
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime

class MartingaleStrategy:
    """Martingale trading strategy implementation"""
    
    def __init__(self, 
                 base_lot_size: float = 0.01,
                 multiplier: float = 2.0,
                 max_levels: int = 5,
                 take_profit_pips: float = 20.0,
                 max_drawdown_percent: float = 10.0,
                 recovery_target_percent: float = 2.0):
        
        self.base_lot_size = base_lot_size
        self.multiplier = multiplier
        self.max_levels = max_levels
        self.take_profit_pips = take_profit_pips
        self.max_drawdown_percent = max_drawdown_percent
        self.recovery_target_percent = recovery_target_percent
        
        self.logger = logging.getLogger(__name__)
        self.current_level = 0
        self.total_loss = 0.0
        self.sequence_active = False
        
    def analyze(self, data: pd.DataFrame, symbol: str = "EURUSD") -> Dict[str, Any]:
        """Analyze market for martingale trading opportunities"""
        try:
            if len(data) < 50:
                return self._no_signal_result("Insufficient data")
            
            current_price = data['close'].iloc[-1]
            
            analysis = self._technical_analysis(data)
            
            signal = self._generate_signal(data, analysis)
            
            position_size = self._calculate_martingale_size()
            
            risk_assessment = self._assess_risk(data)
            
            return {
                'signal': signal,
                'confidence': analysis['confidence'],
                'entry_price': current_price,
                'position_size': position_size,
                'current_level': self.current_level,
                'total_loss': self.total_loss,
                'risk_assessment': risk_assessment,
                'analysis': {
                    'strategy': 'Martingale',
                    'trend_direction': analysis['trend'],
                    'momentum': analysis['momentum'],
                    'volatility': analysis['volatility'],
                    'sequence_active': self.sequence_active,
                    'max_risk_reached': self.current_level >= self.max_levels
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in martingale analysis: {e}")
            return self._no_signal_result(f"Analysis error: {e}")
    
    def _technical_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform technical analysis for signal generation"""
        
        sma_20 = data['close'].rolling(20).mean()
        sma_50 = data['close'].rolling(50).mean()
        ema_12 = data['close'].ewm(span=12).mean()
        ema_26 = data['close'].ewm(span=26).mean()
        
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        macd = ema_12 - ema_26
        macd_signal = macd.ewm(span=9).mean()
        macd_histogram = macd - macd_signal
        
        current_price = data['close'].iloc[-1]
        current_sma_20 = sma_20.iloc[-1]
        current_sma_50 = sma_50.iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_macd = macd.iloc[-1]
        current_macd_signal = macd_signal.iloc[-1]
        
        if current_price > current_sma_20 > current_sma_50:
            trend = 'BULLISH'
        elif current_price < current_sma_20 < current_sma_50:
            trend = 'BEARISH'
        else:
            trend = 'SIDEWAYS'
        
        momentum = 'POSITIVE' if current_macd > current_macd_signal else 'NEGATIVE'
        
        returns = data['close'].pct_change().dropna()
        volatility = returns.tail(20).std()
        
        confidence = 0.5
        if trend != 'SIDEWAYS':
            confidence += 0.2
        if (trend == 'BULLISH' and momentum == 'POSITIVE') or (trend == 'BEARISH' and momentum == 'NEGATIVE'):
            confidence += 0.2
        if 30 < current_rsi < 70:  # Not overbought/oversold
            confidence += 0.1
        
        return {
            'trend': trend,
            'momentum': momentum,
            'volatility': volatility,
            'rsi': current_rsi,
            'macd': current_macd,
            'confidence': min(confidence, 0.9)
        }
    
    def _generate_signal(self, data: pd.DataFrame, analysis: Dict[str, Any]) -> str:
        """Generate trading signal based on analysis"""
        
        if self.current_level >= self.max_levels:
            return 'HOLD'
        
        if analysis['volatility'] > 0.02:
            return 'HOLD'
        
        if analysis['trend'] == 'BULLISH' and analysis['momentum'] == 'POSITIVE':
            if analysis['rsi'] < 70:  # Not overbought
                return 'BUY'
        elif analysis['trend'] == 'BEARISH' and analysis['momentum'] == 'NEGATIVE':
            if analysis['rsi'] > 30:  # Not oversold
                return 'SELL'
        
        if self.sequence_active and self.current_level > 0:
            if analysis['trend'] == 'BULLISH':
                return 'SELL'  # Counter-trend
            elif analysis['trend'] == 'BEARISH':
                return 'BUY'  # Counter-trend
        
        return 'HOLD'
    
    def _calculate_martingale_size(self) -> float:
        """Calculate position size based on martingale level"""
        if self.current_level == 0:
            return self.base_lot_size
        
        return self.base_lot_size * (self.multiplier ** self.current_level)
    
    def _assess_risk(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Assess risk of martingale strategy"""
        
        max_potential_loss = 0
        for level in range(self.max_levels):
            lot_size = self.base_lot_size * (self.multiplier ** level)
            max_potential_loss += lot_size * self.take_profit_pips * 10  # Assuming $10 per pip per lot
        
        current_sequence_risk = 0
        for level in range(self.current_level + 1):
            lot_size = self.base_lot_size * (self.multiplier ** level)
            current_sequence_risk += lot_size * self.take_profit_pips * 10
        
        return {
            'max_potential_loss': max_potential_loss,
            'current_sequence_risk': current_sequence_risk,
            'risk_level': 'HIGH' if self.current_level > 2 else 'MEDIUM' if self.current_level > 0 else 'LOW',
            'levels_remaining': self.max_levels - self.current_level,
            'sequence_active': self.sequence_active
        }
    
    def on_trade_result(self, profit: float, trade_type: str):
        """Update martingale state based on trade result"""
        if profit > 0:
            self.current_level = 0
            self.total_loss = 0.0
            self.sequence_active = False
            self.logger.info(f"Martingale sequence completed with profit: {profit}")
        else:
            self.current_level += 1
            self.total_loss += abs(profit)
            self.sequence_active = True
            self.logger.info(f"Martingale level increased to {self.current_level}, total loss: {self.total_loss}")
            
            if self.current_level >= self.max_levels:
                self.logger.warning("Maximum martingale levels reached - stopping sequence")
    
    def reset_sequence(self):
        """Reset martingale sequence"""
        self.current_level = 0
        self.total_loss = 0.0
        self.sequence_active = False
        self.logger.info("Martingale sequence manually reset")
    
    def calculate_recovery_target(self) -> float:
        """Calculate profit target to recover all losses"""
        if self.total_loss <= 0:
            return self.take_profit_pips
        
        current_lot_size = self._calculate_martingale_size()
        pip_value = current_lot_size * 10  # $10 per pip per lot for EURUSD
        
        required_pips = (self.total_loss / pip_value) + self.take_profit_pips
        return required_pips
    
    def _no_signal_result(self, reason: str) -> Dict[str, Any]:
        """Return no signal result"""
        return {
            'signal': 'HOLD',
            'confidence': 0.0,
            'entry_price': 0.0,
            'reason': reason,
            'current_level': self.current_level,
            'analysis': {
                'strategy': 'Martingale',
                'status': 'No signal',
                'reason': reason
            }
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': 'Martingale Strategy',
            'description': 'Doubles position size after each loss to recover with one win',
            'parameters': {
                'base_lot_size': self.base_lot_size,
                'multiplier': self.multiplier,
                'max_levels': self.max_levels,
                'take_profit_pips': self.take_profit_pips,
                'max_drawdown_percent': self.max_drawdown_percent
            },
            'warnings': [
                'High risk strategy',
                'Can lead to large losses',
                'Requires significant capital',
                'Not suitable for trending markets'
            ],
            'market_conditions': 'Works best in ranging markets with low volatility',
            'risk_level': 'Very High',
            'timeframe': 'M15-H1'
        }
