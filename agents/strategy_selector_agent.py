"""
Strategy selector agent that chooses optimal trading strategies based on market conditions
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from strategies import (
    RSIDivergenceStrategy, MACrossoverStrategy, GridStrategy, MartingaleStrategy,
    LondonBreakoutStrategy, NewsFadeStrategy, NYReversalStrategy, CPIFadeStrategy,
    PullbackStrategy, ScalpingStrategy, TailRiskProtectionStrategy, TrendFollowingStrategy,
    BreakoutReversalStrategy, StochasticStrategy, VaaniV9Strategy
)

import pandas as pd

class MarketRegime(Enum):
    TRENDING = "trending"
    RANGING = "ranging"
    VOLATILE = "volatile"
    QUIET = "quiet"

class StrategyType(Enum):
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    SCALPING = "scalping"
    NEWS_TRADING = "news_trading"
    GRID = "grid"

class StrategySelector:
    """Selects optimal trading strategies based on market conditions"""
    
    def __init__(self, price_feed_manager):
        self.price_feed = price_feed_manager
        self.logger = logging.getLogger(__name__)
        
        self.strategy_performance: Dict[str, Dict] = {}
        self.current_strategy = None
        self.last_switch_time = datetime.now()
        self.min_switch_interval = timedelta(hours=1)  # Minimum time between switches
        
        self.volatility_threshold_high = 0.02
        self.volatility_threshold_low = 0.005
        self.trend_strength_threshold = 0.6
        
        self.available_strategies = {
            "rsi_divergence": RSIDivergenceStrategy,
            "ma_crossover": MACrossoverStrategy,
            "grid": GridStrategy,
            "martingale": MartingaleStrategy,
            "london_breakout": LondonBreakoutStrategy,
            "news_fade": NewsFadeStrategy,
            "ny_reversal": NYReversalStrategy,
            "cpi_fade": CPIFadeStrategy,
            "pullback": PullbackStrategy,
            "scalping": ScalpingStrategy,
            "tail_risk_protection": TailRiskProtectionStrategy,
            "trend_following": TrendFollowingStrategy,
            "breakout_reversal": BreakoutReversalStrategy,
            "stochastic": StochasticStrategy,
            "vaani_v9": VaaniV9Strategy
        }
        
    def select_optimal_strategy(self, symbol: str = "EURUSD") -> Dict[str, Any]:
        """Select the optimal strategy based on current market conditions"""
        try:
            market_regime = self._detect_market_regime(symbol)
            
            recommended_strategies = self._get_strategy_recommendations(market_regime)
            
            best_strategy = self._select_best_performing_strategy(recommended_strategies)
            
            should_switch = self._should_switch_strategy(best_strategy)
            
            result = {
                "current_strategy": self.current_strategy,
                "recommended_strategy": best_strategy,
                "market_regime": market_regime.value,
                "should_switch": should_switch,
                "confidence": self._calculate_confidence(market_regime, best_strategy),
                "reasoning": self._generate_reasoning(market_regime, best_strategy),
                "market_analysis": self._get_market_analysis(symbol)
            }
            
            if should_switch:
                self.current_strategy = best_strategy
                self.last_switch_time = datetime.now()
                self.logger.info(f"Strategy switched to: {best_strategy}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error selecting strategy: {e}")
            return {
                "current_strategy": self.current_strategy or "default",
                "recommended_strategy": "trend_following",
                "market_regime": "unknown",
                "should_switch": False,
                "confidence": 0.5,
                "reasoning": f"Error in strategy selection: {e}",
                "market_analysis": {}
            }
    
    def _detect_market_regime(self, symbol: str) -> MarketRegime:
        """Detect current market regime"""
        try:
            df = self.price_feed.get_historical_data(symbol, "H1", 100)
            if df is None or df.empty:
                return MarketRegime.QUIET
            
            df = self.price_feed.calculate_technical_indicators(df)
            
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(24)  # Annualized hourly volatility
            
            trend_strength = self._calculate_trend_strength(df)
            
            if volatility > self.volatility_threshold_high:
                return MarketRegime.VOLATILE
            elif volatility < self.volatility_threshold_low:
                return MarketRegime.QUIET
            elif trend_strength > self.trend_strength_threshold:
                return MarketRegime.TRENDING
            else:
                return MarketRegime.RANGING
                
        except Exception as e:
            self.logger.error(f"Error detecting market regime: {e}")
            return MarketRegime.QUIET
    
    def _calculate_trend_strength(self, df) -> float:
        """Calculate trend strength using multiple indicators"""
        try:
            if df.empty or len(df) < 50:
                return 0.0
            
            if 'high' in df.columns and 'low' in df.columns and 'close' in df.columns:
                high_low = df['high'] - df['low']
                high_close = np.abs(df['high'] - df['close'].shift())
                low_close = np.abs(df['low'] - df['close'].shift())
                
                true_range = np.maximum(high_low, np.maximum(high_close, low_close))
                atr = true_range.rolling(window=14).mean()
                
                plus_dm = np.where((df['high'] - df['high'].shift()) > (df['low'].shift() - df['low']),
                                 np.maximum(df['high'] - df['high'].shift(), 0), 0)
                minus_dm = np.where((df['low'].shift() - df['low']) > (df['high'] - df['high'].shift()),
                                  np.maximum(df['low'].shift() - df['low'], 0), 0)
                
                plus_di = 100 * (pd.Series(plus_dm).rolling(window=14).mean() / atr)
                minus_di = 100 * (pd.Series(minus_dm).rolling(window=14).mean() / atr)
                
                dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
                adx = dx.rolling(window=14).mean()
                
                return adx.iloc[-1] / 100.0 if not np.isnan(adx.iloc[-1]) else 0.0
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating trend strength: {e}")
            return 0.0
    
    def _get_strategy_recommendations(self, market_regime: MarketRegime) -> List[StrategyType]:
        """Get strategy recommendations based on market regime"""
        recommendations = {
            MarketRegime.TRENDING: [
                StrategyType.TREND_FOLLOWING,
                StrategyType.BREAKOUT,
                StrategyType.NEWS_TRADING
            ],
            MarketRegime.RANGING: [
                StrategyType.MEAN_REVERSION,
                StrategyType.GRID,
                StrategyType.SCALPING
            ],
            MarketRegime.VOLATILE: [
                StrategyType.BREAKOUT,
                StrategyType.NEWS_TRADING,
                StrategyType.SCALPING
            ],
            MarketRegime.QUIET: [
                StrategyType.SCALPING,
                StrategyType.GRID,
                StrategyType.MEAN_REVERSION
            ]
        }
        
        return recommendations.get(market_regime, [StrategyType.TREND_FOLLOWING])
    
    def _select_best_performing_strategy(self, recommended_strategies: List[StrategyType]) -> str:
        """Select best performing strategy from recommendations"""
        if not recommended_strategies:
            return "trend_following"
        
        if not self.strategy_performance:
            return recommended_strategies[0].value
        
        best_strategy = None
        best_score = -float('inf')
        
        for strategy in recommended_strategies:
            strategy_name = strategy.value
            if strategy_name in self.strategy_performance:
                perf = self.strategy_performance[strategy_name]
                score = self._calculate_strategy_score(perf)
                
                if score > best_score:
                    best_score = score
                    best_strategy = strategy_name
        
        return best_strategy or recommended_strategies[0].value
    
    def _calculate_strategy_score(self, performance: Dict) -> float:
        """Calculate strategy performance score"""
        try:
            win_rate = performance.get('win_rate', 0.5)
            avg_profit = performance.get('avg_profit', 0)
            max_drawdown = performance.get('max_drawdown', 0.1)
            total_trades = performance.get('total_trades', 1)
            
            score = (
                win_rate * 0.3 +
                min(avg_profit / 100, 1.0) * 0.3 +
                max(0, 1 - max_drawdown) * 0.2 +
                min(total_trades / 100, 1.0) * 0.2
            )
            
            return score
            
        except Exception as e:
            self.logger.error(f"Error calculating strategy score: {e}")
            return 0.5
    
    def _should_switch_strategy(self, recommended_strategy: str) -> bool:
        """Determine if strategy should be switched"""
        if not self.current_strategy:
            return True
        
        if self.current_strategy == recommended_strategy:
            return False
        
        if datetime.now() - self.last_switch_time < self.min_switch_interval:
            return False
        
        current_score = 0.5
        recommended_score = 0.5
        
        if self.current_strategy in self.strategy_performance:
            current_score = self._calculate_strategy_score(
                self.strategy_performance[self.current_strategy]
            )
        
        if recommended_strategy in self.strategy_performance:
            recommended_score = self._calculate_strategy_score(
                self.strategy_performance[recommended_strategy]
            )
        
        return recommended_score > current_score + 0.1
    
    def _calculate_confidence(self, market_regime: MarketRegime, strategy: str) -> float:
        """Calculate confidence in strategy selection"""
        base_confidence = 0.7
        
        if market_regime in [MarketRegime.TRENDING, MarketRegime.RANGING]:
            base_confidence += 0.1
        elif market_regime == MarketRegime.VOLATILE:
            base_confidence -= 0.1
        
        if strategy in self.strategy_performance:
            perf = self.strategy_performance[strategy]
            if perf.get('total_trades', 0) > 10:
                win_rate = perf.get('win_rate', 0.5)
                if win_rate > 0.6:
                    base_confidence += 0.1
                elif win_rate < 0.4:
                    base_confidence -= 0.1
        
        return max(0.1, min(1.0, base_confidence))
    
    def _generate_reasoning(self, market_regime: MarketRegime, strategy: str) -> str:
        """Generate reasoning for strategy selection"""
        regime_descriptions = {
            MarketRegime.TRENDING: "strong directional movement",
            MarketRegime.RANGING: "sideways price action",
            MarketRegime.VOLATILE: "high volatility conditions",
            MarketRegime.QUIET: "low volatility environment"
        }
        
        strategy_descriptions = {
            "trend_following": "follows market momentum",
            "mean_reversion": "trades price reversals to mean",
            "breakout": "captures price breakouts",
            "scalping": "quick small profit trades",
            "news_trading": "trades news-driven moves",
            "grid": "systematic buy/sell levels"
        }
        
        regime_desc = regime_descriptions.get(market_regime, "current market conditions")
        strategy_desc = strategy_descriptions.get(strategy, "selected approach")
        
        return f"Market shows {regime_desc}. {strategy.replace('_', ' ').title()} strategy selected as it {strategy_desc} which is optimal for these conditions."
    
    def _get_market_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get detailed market analysis"""
        try:
            df = self.price_feed.get_historical_data(symbol, "H1", 50)
            if df is None or df.empty:
                return {}
            
            df = self.price_feed.calculate_technical_indicators(df)
            latest = df.iloc[-1]
            
            return {
                "price": latest.get('close', 0),
                "rsi": latest.get('rsi', 50),
                "macd": latest.get('macd', 0),
                "atr": latest.get('atr', 0),
                "sma_20": latest.get('sma_20', 0),
                "sma_50": latest.get('sma_50', 0),
                "volatility": self.price_feed.get_volatility_metrics(symbol).get('recent_volatility', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting market analysis: {e}")
            return {}
    
    def update_strategy_performance(self, strategy: str, trade_result: Dict):
        """Update strategy performance tracking"""
        try:
            if strategy not in self.strategy_performance:
                self.strategy_performance[strategy] = {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'total_profit': 0,
                    'max_drawdown': 0,
                    'last_updated': datetime.now()
                }
            
            perf = self.strategy_performance[strategy]
            perf['total_trades'] += 1
            
            profit = trade_result.get('profit', 0)
            perf['total_profit'] += profit
            
            if profit > 0:
                perf['winning_trades'] += 1
            
            perf['win_rate'] = perf['winning_trades'] / perf['total_trades']
            perf['avg_profit'] = perf['total_profit'] / perf['total_trades']
            perf['last_updated'] = datetime.now()
            
            self.logger.info(f"Updated performance for {strategy}: {perf}")
            
        except Exception as e:
            self.logger.error(f"Error updating strategy performance: {e}")
    
    def get_strategy_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive strategy performance report"""
        return {
            "current_strategy": self.current_strategy,
            "last_switch_time": self.last_switch_time.isoformat() if self.last_switch_time else None,
            "strategy_performance": self.strategy_performance,
            "total_strategies_tested": len(self.strategy_performance)
        }
