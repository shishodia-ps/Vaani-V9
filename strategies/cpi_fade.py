"""
CPI Fade Trading Strategy
Specialized strategy for trading CPI (Consumer Price Index) announcements
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, time

class CPIFadeStrategy:
    """CPI announcement fade trading strategy"""
    
    def __init__(self, 
                 cpi_release_times: Optional[List[str]] = None,
                 pre_announcement_window: int = 60,
                 post_announcement_window: int = 120,
                 volatility_spike_threshold: float = 0.02,
                 fade_delay_minutes: int = 15,
                 stop_loss_pips: float = 40.0,
                 take_profit_pips: float = 30.0):
        
        self.cpi_release_times = cpi_release_times or ["08:30", "14:30"]
        self.pre_announcement_window = pre_announcement_window
        self.post_announcement_window = post_announcement_window
        self.volatility_spike_threshold = volatility_spike_threshold
        self.fade_delay_minutes = fade_delay_minutes
        self.stop_loss_pips = stop_loss_pips
        self.take_profit_pips = take_profit_pips
        
        self.logger = logging.getLogger(__name__)
        self.last_cpi_time = None
        self.announcement_detected = False
        
    def analyze(self, data: pd.DataFrame, symbol: str = "EURUSD") -> Dict[str, Any]:
        """Analyze market for CPI fade opportunities"""
        try:
            if len(data) < 200:
                return self._no_signal_result("Insufficient data")
            
            current_time = datetime.now()
            current_price = data['close'].iloc[-1]
            
            cpi_timing = self._analyze_cpi_timing(current_time)
            
            if not cpi_timing['relevant_period']:
                return self._no_signal_result("Outside CPI trading window")
            
            volatility_analysis = self._analyze_cpi_volatility(data)
            
            announcement_impact = self._detect_cpi_announcement(data, volatility_analysis)
            
            fade_signal = self._evaluate_fade_opportunity(data, announcement_impact, cpi_timing)
            
            return {
                'signal': fade_signal['signal'],
                'confidence': fade_signal['confidence'],
                'entry_price': current_price,
                'cpi_detected': announcement_impact['announcement_detected'],
                'volatility_spike': volatility_analysis['spike_detected'],
                'time_to_cpi': cpi_timing['time_to_release'],
                'fade_conditions': fade_signal['conditions_met'],
                'analysis': {
                    'strategy': 'CPI Fade',
                    'cpi_period': cpi_timing['period_type'],
                    'volatility_level': volatility_analysis['current_level'],
                    'spike_magnitude': announcement_impact['spike_magnitude'],
                    'market_condition': self._assess_market_condition(data)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in CPI fade analysis: {e}")
            return self._no_signal_result(f"Analysis error: {e}")
    
    def _analyze_cpi_timing(self, current_time: datetime) -> Dict[str, Any]:
        """Analyze timing relative to CPI announcements"""
        
        current_time_str = current_time.strftime("%H:%M")
        
        for release_time in self.cpi_release_times:
            release_hour, release_minute = map(int, release_time.split(":"))
            release_datetime = current_time.replace(hour=release_hour, minute=release_minute, second=0, microsecond=0)
            
            time_diff = (current_time - release_datetime).total_seconds() / 60
            
            if -self.pre_announcement_window <= time_diff <= self.post_announcement_window:
                if time_diff < 0:
                    period_type = "Pre-announcement"
                elif time_diff <= self.fade_delay_minutes:
                    period_type = "Immediate post-announcement"
                else:
                    period_type = "Fade window"
                
                return {
                    'relevant_period': True,
                    'period_type': period_type,
                    'time_to_release': time_diff,
                    'release_time': release_time
                }
        
        return {
            'relevant_period': False,
            'period_type': 'Outside CPI window',
            'time_to_release': None,
            'release_time': None
        }
    
    def _analyze_cpi_volatility(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volatility patterns around CPI"""
        
        returns = data['close'].pct_change().dropna()
        
        current_volatility = returns.tail(20).std()
        baseline_volatility = returns.tail(100).std()
        
        volatility_ratio = current_volatility / baseline_volatility if baseline_volatility > 0 else 1.0
        
        spike_detected = current_volatility > self.volatility_spike_threshold
        
        recent_high_vol_periods = (returns.tail(60).abs() > self.volatility_spike_threshold).sum()
        
        return {
            'current_level': current_volatility,
            'baseline_level': baseline_volatility,
            'volatility_ratio': volatility_ratio,
            'spike_detected': spike_detected,
            'recent_spikes': recent_high_vol_periods
        }
    
    def _detect_cpi_announcement(self, data: pd.DataFrame, volatility_info: Dict) -> Dict[str, Any]:
        """Detect CPI announcement impact on price"""
        
        if not volatility_info['spike_detected']:
            return {
                'announcement_detected': False,
                'spike_magnitude': 0,
                'price_direction': 'None'
            }
        
        recent_data = data.tail(30)
        
        max_move_up = (recent_data['high'].max() - recent_data['close'].iloc[0]) / recent_data['close'].iloc[0]
        max_move_down = (recent_data['close'].iloc[0] - recent_data['low'].min()) / recent_data['close'].iloc[0]
        
        if max_move_up > max_move_down:
            spike_magnitude = max_move_up
            price_direction = 'Up'
        else:
            spike_magnitude = max_move_down
            price_direction = 'Down'
        
        announcement_detected = spike_magnitude > 0.005
        
        return {
            'announcement_detected': announcement_detected,
            'spike_magnitude': spike_magnitude,
            'price_direction': price_direction
        }
    
    def _evaluate_fade_opportunity(self, data: pd.DataFrame, announcement_info: Dict, timing_info: Dict) -> Dict[str, Any]:
        """Evaluate fade trading opportunity"""
        
        if timing_info['period_type'] != "Fade window":
            return {'signal': 'HOLD', 'confidence': 0.0, 'conditions_met': False}
        
        if not announcement_info['announcement_detected']:
            return {'signal': 'HOLD', 'confidence': 0.0, 'conditions_met': False}
        
        current_price = data['close'].iloc[-1]
        
        sma_20 = data['close'].rolling(20).mean().iloc[-1]
        sma_50 = data['close'].rolling(50).mean().iloc[-1]
        
        confidence = 0.6
        
        if announcement_info['spike_magnitude'] > 0.01:
            confidence += 0.2
        
        if timing_info['time_to_release'] > 30:
            confidence += 0.1
        
        price_vs_sma20 = (current_price - sma_20) / sma_20
        
        if announcement_info['price_direction'] == 'Up' and price_vs_sma20 > 0.002:
            return {
                'signal': 'SELL',
                'confidence': min(confidence, 0.9),
                'conditions_met': True,
                'fade_reason': 'Fading upward CPI spike'
            }
        elif announcement_info['price_direction'] == 'Down' and price_vs_sma20 < -0.002:
            return {
                'signal': 'BUY',
                'confidence': min(confidence, 0.9),
                'conditions_met': True,
                'fade_reason': 'Fading downward CPI spike'
            }
        
        return {'signal': 'HOLD', 'confidence': 0.0, 'conditions_met': False}
    
    def _assess_market_condition(self, data: pd.DataFrame) -> str:
        """Assess market condition for CPI trading"""
        if len(data) < 50:
            return "Insufficient data"
        
        returns = data['close'].pct_change().dropna()
        volatility = returns.tail(20).std()
        
        if volatility > self.volatility_spike_threshold:
            return "High volatility - CPI impact detected"
        elif volatility > 0.01:
            return "Elevated volatility - Pre-CPI positioning"
        else:
            return "Normal volatility - Awaiting CPI"
    
    def _no_signal_result(self, reason: str) -> Dict[str, Any]:
        """Return no signal result"""
        return {
            'signal': 'HOLD',
            'confidence': 0.0,
            'entry_price': 0.0,
            'reason': reason,
            'analysis': {
                'strategy': 'CPI Fade',
                'status': 'No signal',
                'reason': reason
            }
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': 'CPI Fade Strategy',
            'description': 'Specialized strategy for trading CPI announcements',
            'parameters': {
                'cpi_release_times': self.cpi_release_times,
                'pre_announcement_window': self.pre_announcement_window,
                'post_announcement_window': self.post_announcement_window,
                'volatility_spike_threshold': self.volatility_spike_threshold,
                'fade_delay_minutes': self.fade_delay_minutes,
                'stop_loss_pips': self.stop_loss_pips,
                'take_profit_pips': self.take_profit_pips
            },
            'market_conditions': 'Active only around CPI announcement times',
            'risk_level': 'High',
            'timeframe': 'M1-M15',
            'suitable_for': ['news_trading', 'economic_events'],
            'warnings': [
                'High risk during news events',
                'Requires precise timing',
                'Use with economic calendar'
            ]
        }
