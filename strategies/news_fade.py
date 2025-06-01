"""
News Fade Trading Strategy
Fades initial news reactions, betting on mean reversion after news spikes
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, time

class NewsFadeStrategy:
    """News fade trading strategy implementation"""
    
    def __init__(self, 
                 volatility_threshold: float = 0.015,
                 fade_window_minutes: int = 30,
                 min_spike_percent: float = 0.5,
                 max_fade_distance: float = 0.002,
                 stop_loss_pips: float = 30.0,
                 take_profit_pips: float = 20.0):
        
        self.volatility_threshold = volatility_threshold
        self.fade_window_minutes = fade_window_minutes
        self.min_spike_percent = min_spike_percent
        self.max_fade_distance = max_fade_distance
        self.stop_loss_pips = stop_loss_pips
        self.take_profit_pips = take_profit_pips
        
        self.logger = logging.getLogger(__name__)
        self.news_times = []
        self.last_spike_time = None
        
    def analyze(self, data: pd.DataFrame, symbol: str = "EURUSD") -> Dict[str, Any]:
        """Analyze market for news fade opportunities"""
        try:
            if len(data) < 100:
                return self._no_signal_result("Insufficient data")
            
            current_price = data['close'].iloc[-1]
            
            volatility_analysis = self._analyze_volatility(data)
            
            spike_detection = self._detect_news_spike(data)
            
            fade_signal = self._evaluate_fade_opportunity(data, spike_detection, volatility_analysis)
            
            return {
                'signal': fade_signal['signal'],
                'confidence': fade_signal['confidence'],
                'entry_price': current_price,
                'volatility_spike': spike_detection['spike_detected'],
                'spike_magnitude': spike_detection['magnitude'],
                'time_since_spike': spike_detection['time_since_spike'],
                'analysis': {
                    'strategy': 'News Fade',
                    'current_volatility': volatility_analysis['current_volatility'],
                    'volatility_percentile': volatility_analysis['percentile'],
                    'fade_conditions_met': fade_signal['conditions_met'],
                    'market_condition': self._assess_market_condition(data)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in news fade analysis: {e}")
            return self._no_signal_result(f"Analysis error: {e}")
    
    def _analyze_volatility(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze current volatility conditions"""
        
        returns = data['close'].pct_change().dropna()
        
        current_volatility = returns.tail(20).std()
        
        rolling_volatility = returns.rolling(100).std()
        volatility_percentile = (rolling_volatility.iloc[-1] > rolling_volatility).mean()
        
        volatility_spike = current_volatility > self.volatility_threshold
        
        return {
            'current_volatility': current_volatility,
            'percentile': volatility_percentile,
            'spike_detected': volatility_spike,
            'threshold': self.volatility_threshold
        }
    
    def _detect_news_spike(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect recent news-driven price spikes"""
        
        if len(data) < 50:
            return {'spike_detected': False, 'magnitude': 0, 'time_since_spike': None}
        
        recent_data = data.tail(50)
        
        price_changes = recent_data['close'].pct_change().abs()
        
        spike_threshold = price_changes.quantile(0.95)
        
        recent_spikes = price_changes[price_changes > max(spike_threshold, self.min_spike_percent / 100)]
        
        if len(recent_spikes) > 0:
            last_spike_idx = recent_spikes.index[-1]
            try:
                spike_position = recent_data.index.get_loc(last_spike_idx)
                if isinstance(spike_position, slice):
                    spike_position = spike_position.start
                elif isinstance(spike_position, (list, tuple, np.ndarray)) and len(spike_position) > 0:
                    spike_position = spike_position[0]
                time_since_spike = len(recent_data) - int(spike_position) - 1
            except (TypeError, IndexError, AttributeError):
                time_since_spike = 5
            
            return {
                'spike_detected': True,
                'magnitude': recent_spikes.iloc[-1],
                'time_since_spike': time_since_spike,
                'spike_index': last_spike_idx
            }
        
        return {'spike_detected': False, 'magnitude': 0, 'time_since_spike': None}
    
    def _evaluate_fade_opportunity(self, data: pd.DataFrame, spike_info: Dict, volatility_info: Dict) -> Dict[str, Any]:
        """Evaluate if conditions are right for a fade trade"""
        
        if not spike_info['spike_detected']:
            return {'signal': 'HOLD', 'confidence': 0.0, 'conditions_met': False}
        
        time_since_spike = spike_info['time_since_spike']
        if time_since_spike is None or time_since_spike > self.fade_window_minutes:
            return {'signal': 'HOLD', 'confidence': 0.0, 'conditions_met': False}
        
        current_price = data['close'].iloc[-1]
        
        if spike_info['spike_index'] in data.index:
            spike_price = data.loc[spike_info['spike_index'], 'close']
            
            price_distance = abs(current_price - spike_price) / spike_price
            
            if price_distance > self.max_fade_distance:
                return {'signal': 'HOLD', 'confidence': 0.0, 'conditions_met': False}
            
            sma_20 = data['close'].rolling(20).mean().iloc[-1]
            
            confidence = 0.6
            
            if volatility_info['percentile'] > 0.8:
                confidence += 0.2
            
            if time_since_spike < 10:
                confidence += 0.1
            
            if current_price > spike_price and current_price > sma_20:
                return {'signal': 'SELL', 'confidence': min(confidence, 0.9), 'conditions_met': True}
            elif current_price < spike_price and current_price < sma_20:
                return {'signal': 'BUY', 'confidence': min(confidence, 0.9), 'conditions_met': True}
        
        return {'signal': 'HOLD', 'confidence': 0.0, 'conditions_met': False}
    
    def _assess_market_condition(self, data: pd.DataFrame) -> str:
        """Assess current market condition"""
        if len(data) < 50:
            return "Insufficient data"
        
        sma_20 = data['close'].rolling(20).mean()
        sma_50 = data['close'].rolling(50).mean()
        
        current_price = data['close'].iloc[-1]
        sma_20_current = sma_20.iloc[-1]
        sma_50_current = sma_50.iloc[-1]
        
        returns = data['close'].pct_change().dropna()
        volatility = returns.tail(20).std()
        
        if volatility > self.volatility_threshold:
            return "High volatility - Good for fading"
        elif current_price > sma_20_current > sma_50_current:
            return "Uptrend - Fade resistance"
        elif current_price < sma_20_current < sma_50_current:
            return "Downtrend - Fade support"
        else:
            return "Ranging - Neutral"
    
    def _no_signal_result(self, reason: str) -> Dict[str, Any]:
        """Return no signal result"""
        return {
            'signal': 'HOLD',
            'confidence': 0.0,
            'entry_price': 0.0,
            'reason': reason,
            'analysis': {
                'strategy': 'News Fade',
                'status': 'No signal',
                'reason': reason
            }
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': 'News Fade Strategy',
            'description': 'Fades initial news reactions betting on mean reversion',
            'parameters': {
                'volatility_threshold': self.volatility_threshold,
                'fade_window_minutes': self.fade_window_minutes,
                'min_spike_percent': self.min_spike_percent,
                'max_fade_distance': self.max_fade_distance,
                'stop_loss_pips': self.stop_loss_pips,
                'take_profit_pips': self.take_profit_pips
            },
            'market_conditions': 'Works best during high volatility news events',
            'risk_level': 'Medium to High',
            'timeframe': 'M1-M15',
            'suitable_for': ['news_events', 'high_volatility'],
            'warnings': [
                'Requires quick execution',
                'High risk during trending news',
                'Best used with economic calendar'
            ]
        }
