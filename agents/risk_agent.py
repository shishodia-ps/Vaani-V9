"""
Risk management agent for monitoring and controlling trading risk
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class RiskMetrics:
    """Risk metrics data structure"""
    current_drawdown: float
    daily_pnl: float
    open_positions: int
    margin_level: float
    risk_per_trade: float
    total_exposure: float
    correlation_risk: float
    volatility_risk: float
    news_risk: float

class RiskAgent:
    """Monitors and manages trading risk"""
    
    def __init__(self, trade_executor, config):
        self.trade_executor = trade_executor
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.max_drawdown = config.trading.max_drawdown_percent
        self.max_daily_loss = config.trading.get('max_daily_loss_percent', 5.0)
        self.max_positions = config.trading.get('max_positions', 5)
        self.min_margin_level = config.trading.get('min_margin_level', 200.0)
        self.max_correlation = config.trading.get('max_correlation', 0.7)
        
        self.risk_alerts: List[Dict] = []
        self.emergency_stop_triggered = False
        self.last_risk_check = datetime.now()
        
    def assess_risk(self) -> Dict[str, Any]:
        """Comprehensive risk assessment"""
        try:
            metrics = self._calculate_risk_metrics()
            
            risk_assessment = {
                "overall_risk_level": self._calculate_overall_risk(metrics),
                "risk_metrics": metrics.__dict__,
                "risk_alerts": self._check_risk_alerts(metrics),
                "recommendations": self._generate_recommendations(metrics),
                "emergency_actions": self._check_emergency_conditions(metrics),
                "timestamp": datetime.now().isoformat()
            }
            
            self.last_risk_check = datetime.now()
            
            return risk_assessment
            
        except Exception as e:
            self.logger.error(f"Error in risk assessment: {e}")
            return {
                "overall_risk_level": RiskLevel.HIGH.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _calculate_risk_metrics(self) -> RiskMetrics:
        """Calculate current risk metrics"""
        try:
            account_info = self.trade_executor.mt5_interface.get_account_info()
            if not account_info:
                return RiskMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0)
            
            current_drawdown = ((account_info.balance - account_info.equity) / account_info.balance) * 100
            
            positions = self.trade_executor.get_open_positions()
            
            trade_stats = self.trade_executor.get_trade_statistics()
            daily_pnl = trade_stats.get('daily_pnl', 0)
            
            total_exposure = sum(pos.get('volume', 0) for pos in positions)
            
            correlation_risk = self._calculate_correlation_risk(positions)
            
            volatility_risk = self._calculate_volatility_risk(positions)
            
            news_risk = 0.0  # Would be calculated based on upcoming news events
            
            return RiskMetrics(
                current_drawdown=abs(current_drawdown),
                daily_pnl=daily_pnl,
                open_positions=len(positions),
                margin_level=account_info.margin_level or 0,
                risk_per_trade=self.config.trading.default_risk_percent,
                total_exposure=total_exposure,
                correlation_risk=correlation_risk,
                volatility_risk=volatility_risk,
                news_risk=news_risk
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {e}")
            return RiskMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0)
    
    def _calculate_overall_risk(self, metrics: RiskMetrics) -> str:
        """Calculate overall risk level"""
        risk_score = 0
        
        if metrics.current_drawdown > self.max_drawdown * 0.8:
            risk_score += 3
        elif metrics.current_drawdown > self.max_drawdown * 0.5:
            risk_score += 2
        elif metrics.current_drawdown > self.max_drawdown * 0.3:
            risk_score += 1
        
        daily_loss_pct = abs(metrics.daily_pnl) / 1000  # Assuming $1000 account for calculation
        if daily_loss_pct > self.max_daily_loss * 0.8:
            risk_score += 3
        elif daily_loss_pct > self.max_daily_loss * 0.5:
            risk_score += 2
        
        if metrics.open_positions > self.max_positions:
            risk_score += 2
        elif metrics.open_positions > self.max_positions * 0.8:
            risk_score += 1
        
        if metrics.margin_level < self.min_margin_level:
            risk_score += 3
        elif metrics.margin_level < self.min_margin_level * 1.5:
            risk_score += 2
        
        if metrics.correlation_risk > self.max_correlation:
            risk_score += 2
        elif metrics.correlation_risk > self.max_correlation * 0.8:
            risk_score += 1
        
        if metrics.volatility_risk > 0.8:
            risk_score += 2
        elif metrics.volatility_risk > 0.6:
            risk_score += 1
        
        if risk_score >= 8:
            return RiskLevel.CRITICAL.value
        elif risk_score >= 5:
            return RiskLevel.HIGH.value
        elif risk_score >= 2:
            return RiskLevel.MEDIUM.value
        else:
            return RiskLevel.LOW.value
    
    def _check_risk_alerts(self, metrics: RiskMetrics) -> List[Dict]:
        """Check for risk alerts"""
        alerts = []
        
        if metrics.current_drawdown > self.max_drawdown * 0.7:
            alerts.append({
                "type": "drawdown_warning",
                "severity": "high" if metrics.current_drawdown > self.max_drawdown * 0.9 else "medium",
                "message": f"Current drawdown {metrics.current_drawdown:.2f}% approaching limit {self.max_drawdown}%",
                "timestamp": datetime.now().isoformat()
            })
        
        daily_loss_pct = abs(metrics.daily_pnl) / 1000  # Assuming $1000 account
        if daily_loss_pct > self.max_daily_loss * 0.7:
            alerts.append({
                "type": "daily_loss_warning",
                "severity": "high" if daily_loss_pct > self.max_daily_loss * 0.9 else "medium",
                "message": f"Daily loss {daily_loss_pct:.2f}% approaching limit {self.max_daily_loss}%",
                "timestamp": datetime.now().isoformat()
            })
        
        if metrics.open_positions > self.max_positions * 0.8:
            alerts.append({
                "type": "position_count_warning",
                "severity": "medium",
                "message": f"Open positions {metrics.open_positions} approaching limit {self.max_positions}",
                "timestamp": datetime.now().isoformat()
            })
        
        if metrics.margin_level < self.min_margin_level * 1.2:
            alerts.append({
                "type": "margin_warning",
                "severity": "high" if metrics.margin_level < self.min_margin_level else "medium",
                "message": f"Margin level {metrics.margin_level:.2f}% below safe threshold",
                "timestamp": datetime.now().isoformat()
            })
        
        if metrics.correlation_risk > self.max_correlation * 0.8:
            alerts.append({
                "type": "correlation_warning",
                "severity": "medium",
                "message": f"High correlation risk {metrics.correlation_risk:.2f} detected",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
    
    def _generate_recommendations(self, metrics: RiskMetrics) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []
        
        if metrics.current_drawdown > self.max_drawdown * 0.5:
            recommendations.append("Consider reducing position sizes")
            recommendations.append("Review and tighten stop losses")
        
        if metrics.open_positions > self.max_positions * 0.8:
            recommendations.append("Avoid opening new positions")
            recommendations.append("Consider closing some existing positions")
        
        if metrics.margin_level < self.min_margin_level * 1.5:
            recommendations.append("Close some positions to improve margin")
            recommendations.append("Avoid high-leverage trades")
        
        if metrics.correlation_risk > self.max_correlation * 0.7:
            recommendations.append("Diversify positions across different currency pairs")
            recommendations.append("Avoid correlated trades")
        
        if metrics.volatility_risk > 0.6:
            recommendations.append("Reduce position sizes during high volatility")
            recommendations.append("Use wider stop losses")
        
        return recommendations
    
    def _check_emergency_conditions(self, metrics: RiskMetrics) -> List[str]:
        """Check for emergency stop conditions"""
        emergency_actions = []
        
        if metrics.current_drawdown >= self.max_drawdown:
            emergency_actions.append("EMERGENCY: Maximum drawdown reached - halt all trading")
            self.emergency_stop_triggered = True
        
        if metrics.margin_level <= self.min_margin_level:
            emergency_actions.append("EMERGENCY: Margin call risk - close positions immediately")
        
        daily_loss_pct = abs(metrics.daily_pnl) / 1000  # Assuming $1000 account
        if daily_loss_pct >= self.max_daily_loss:
            emergency_actions.append("EMERGENCY: Daily loss limit reached - stop trading for today")
        
        return emergency_actions
    
    def _calculate_correlation_risk(self, positions: List[Dict]) -> float:
        """Calculate correlation risk between positions"""
        if len(positions) < 2:
            return 0.0
        
        try:
            symbols = [pos.get('symbol', '') for pos in positions]
            
            currency_exposure = {}
            for symbol in symbols:
                if len(symbol) >= 6:
                    base = symbol[:3]
                    quote = symbol[3:6]
                    
                    currency_exposure[base] = currency_exposure.get(base, 0) + 1
                    currency_exposure[quote] = currency_exposure.get(quote, 0) + 1
            
            max_exposure = max(currency_exposure.values()) if currency_exposure else 0
            total_positions = len(positions)
            
            return min(1.0, max_exposure / total_positions) if total_positions > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating correlation risk: {e}")
            return 0.5  # Default medium risk
    
    def _calculate_volatility_risk(self, positions: List[Dict]) -> float:
        """Calculate volatility risk of current positions"""
        if not positions:
            return 0.0
        
        try:
            
            total_risk = 0.0
            for pos in positions:
                symbol = pos.get('symbol', '')
                volume = pos.get('volume', 0)
                
                if 'JPY' in symbol:
                    pair_risk = 0.6  # JPY pairs typically more volatile
                elif 'GBP' in symbol:
                    pair_risk = 0.7  # GBP pairs can be volatile
                elif 'EUR' in symbol or 'USD' in symbol:
                    pair_risk = 0.4  # Major pairs less volatile
                else:
                    pair_risk = 0.8  # Exotic pairs more volatile
                
                total_risk += pair_risk * volume
            
            return min(1.0, total_risk / len(positions))
            
        except Exception as e:
            self.logger.error(f"Error calculating volatility risk: {e}")
            return 0.5
    
    def should_allow_new_trade(self, trade_signal) -> Dict[str, Any]:
        """Check if new trade should be allowed based on risk"""
        try:
            metrics = self._calculate_risk_metrics()
            
            if self.emergency_stop_triggered:
                return {
                    "allowed": False,
                    "reason": "Emergency stop is active",
                    "risk_level": RiskLevel.CRITICAL.value
                }
            
            if metrics.open_positions >= self.max_positions:
                return {
                    "allowed": False,
                    "reason": f"Maximum positions ({self.max_positions}) reached",
                    "risk_level": RiskLevel.HIGH.value
                }
            
            if metrics.current_drawdown > self.max_drawdown * 0.8:
                return {
                    "allowed": False,
                    "reason": f"Drawdown {metrics.current_drawdown:.2f}% too high",
                    "risk_level": RiskLevel.HIGH.value
                }
            
            if metrics.margin_level < self.min_margin_level * 1.2:
                return {
                    "allowed": False,
                    "reason": f"Margin level {metrics.margin_level:.2f}% too low",
                    "risk_level": RiskLevel.HIGH.value
                }
            
            symbol = trade_signal.symbol
            positions = self.trade_executor.get_open_positions()
            
            correlated_positions = 0
            for pos in positions:
                if self._are_pairs_correlated(symbol, pos.get('symbol', '')):
                    correlated_positions += 1
            
            if correlated_positions >= 2:  # Max 2 correlated positions
                return {
                    "allowed": False,
                    "reason": f"Too many correlated positions with {symbol}",
                    "risk_level": RiskLevel.MEDIUM.value
                }
            
            return {
                "allowed": True,
                "reason": "Risk checks passed",
                "risk_level": self._calculate_overall_risk(metrics)
            }
            
        except Exception as e:
            self.logger.error(f"Error checking trade permission: {e}")
            return {
                "allowed": False,
                "reason": f"Risk check error: {e}",
                "risk_level": RiskLevel.HIGH.value
            }
    
    def _are_pairs_correlated(self, symbol1: str, symbol2: str) -> bool:
        """Check if two currency pairs are correlated"""
        if symbol1 == symbol2:
            return True
        
        if len(symbol1) < 6 or len(symbol2) < 6:
            return False
        
        base1, quote1 = symbol1[:3], symbol1[3:6]
        base2, quote2 = symbol2[:3], symbol2[3:6]
        
        shared_currencies = len(set([base1, quote1]) & set([base2, quote2]))
        
        return shared_currencies > 0
    
    def get_risk_report(self) -> Dict[str, Any]:
        """Get comprehensive risk report"""
        assessment = self.assess_risk()
        
        return {
            "risk_assessment": assessment,
            "risk_alerts": self.risk_alerts,
            "emergency_stop_active": self.emergency_stop_triggered,
            "last_check": self.last_risk_check.isoformat(),
            "risk_thresholds": {
                "max_drawdown": self.max_drawdown,
                "max_daily_loss": self.max_daily_loss,
                "max_positions": self.max_positions,
                "min_margin_level": self.min_margin_level,
                "max_correlation": self.max_correlation
            }
        }
    
    def reset_emergency_stop(self):
        """Reset emergency stop (manual intervention)"""
        self.emergency_stop_triggered = False
        self.logger.info("Emergency stop reset manually")
    
    def update_risk_thresholds(self, new_thresholds: Dict[str, float]):
        """Update risk management thresholds"""
        for key, value in new_thresholds.items():
            if hasattr(self, key):
                setattr(self, key, value)
                self.logger.info(f"Updated {key} to {value}")
