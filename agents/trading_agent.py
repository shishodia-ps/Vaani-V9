"""
Main trading agent that coordinates strategy execution and trade decisions
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

from core.config_loader import config
from core.trade_executor import TradeExecutor, TradeSignal, TradeDirection
from core.price_feed import PriceFeedManager
from .llm_reasoner_agent import LLMReasonerAgent

@dataclass
class TradingContext:
    """Current trading context and market state"""
    symbol: str
    current_price: float
    market_session: str
    volatility: float
    trend_direction: str
    support_resistance: Dict[str, float]
    economic_events: List[Dict]
    open_positions: List[Dict]
    account_equity: float
    daily_pnl: float

class TradingAgent:
    """Main trading agent that makes trading decisions"""
    
    def __init__(self, trade_executor: TradeExecutor, price_feed: PriceFeedManager):
        self.trade_executor = trade_executor
        self.price_feed = price_feed
        self.llm_reasoner = LLMReasonerAgent()
        self.logger = logging.getLogger(__name__)
        
        self.active_strategies: List[str] = []
        self.current_context: Optional[TradingContext] = None
        self.last_decision_time = datetime.now()
        self.decision_cooldown = timedelta(minutes=5)
        
        self.is_trading_enabled = config.trading.trading_enabled
        self.max_positions = 3
        self.risk_per_trade = config.trading.default_risk_percent
        
    async def analyze_market_and_trade(self, symbol: str = "EURUSD") -> Dict[str, Any]:
        """Main trading loop - analyze market and make trading decisions"""
        try:
            if datetime.now() - self.last_decision_time < self.decision_cooldown:
                return {"status": "waiting", "message": "Decision cooldown active"}
            
            context = await self._gather_trading_context(symbol)
            if not context:
                return {"status": "error", "message": "Failed to gather market context"}
            
            self.current_context = context
            
            if not self._should_trade(context):
                return {"status": "no_trade", "context": context.__dict__}
            
            llm_analysis = await self.llm_reasoner.analyze_trading_opportunity(context)
            
            decision = await self._make_trading_decision(context, llm_analysis)
            
            self.last_decision_time = datetime.now()
            
            return {
                "status": "decision_made",
                "context": context.__dict__,
                "llm_analysis": llm_analysis,
                "decision": decision
            }
            
        except Exception as e:
            self.logger.error(f"Error in trading analysis: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _gather_trading_context(self, symbol: str) -> Optional[TradingContext]:
        """Gather all relevant trading context"""
        try:
            price_tick = self.price_feed.get_current_price(symbol)
            if not price_tick:
                return None
            
            market_info = self.price_feed.get_market_hours(symbol)
            
            volatility_metrics = self.price_feed.get_volatility_metrics(symbol)
            
            df = self.price_feed.get_historical_data(symbol, "H1", 100)
            if df is None or df.empty:
                return None
            
            df = self.price_feed.calculate_technical_indicators(df)
            
            trend_direction = self._determine_trend(df)
            
            support_resistance = self._find_support_resistance(df)
            
            account_info = self.trade_executor.mt5_interface.get_account_info()
            if not account_info:
                return None
            
            open_positions = self.trade_executor.get_open_positions()
            
            trade_stats = self.trade_executor.get_trade_statistics()
            
            return TradingContext(
                symbol=symbol,
                current_price=price_tick.bid,
                market_session=market_info.get('session', 'unknown'),
                volatility=volatility_metrics.get('recent_volatility', 0),
                trend_direction=trend_direction,
                support_resistance=support_resistance,
                economic_events=[],  # Would be populated by macro event agent
                open_positions=open_positions,
                account_equity=account_info.equity,
                daily_pnl=trade_stats.get('current_pnl', 0)
            )
            
        except Exception as e:
            self.logger.error(f"Error gathering trading context: {e}")
            return None
    
    def _determine_trend(self, df) -> str:
        """Determine current trend direction"""
        if df.empty or 'sma_20' not in df.columns or 'sma_50' not in df.columns:
            return "sideways"
        
        current_price = df['close'].iloc[-1]
        sma_20 = df['sma_20'].iloc[-1]
        sma_50 = df['sma_50'].iloc[-1]
        
        if current_price > sma_20 > sma_50:
            return "uptrend"
        elif current_price < sma_20 < sma_50:
            return "downtrend"
        else:
            return "sideways"
    
    def _find_support_resistance(self, df) -> Dict[str, float]:
        """Find key support and resistance levels"""
        if df.empty:
            return {"support": 0, "resistance": 0}
        
        recent_data = df.tail(50)
        
        resistance = recent_data['high'].max()
        support = recent_data['low'].min()
        
        return {
            "support": support,
            "resistance": resistance,
            "current_support": recent_data['low'].tail(10).min(),
            "current_resistance": recent_data['high'].tail(10).max()
        }
    
    def _should_trade(self, context: TradingContext) -> bool:
        """Check if trading conditions are met"""
        if not self.is_trading_enabled:
            return False
        
        if context.market_session == 'closed':
            return False
        
        if len(context.open_positions) >= self.max_positions:
            return False
        
        if context.account_equity <= 0:
            return False
        
        if context.volatility > 0.05:  # 5% volatility threshold
            return False
        
        return True
    
    async def _make_trading_decision(self, context: TradingContext, llm_analysis: Dict) -> Dict[str, Any]:
        """Make final trading decision based on context and LLM analysis"""
        try:
            recommendation = llm_analysis.get('recommendation', 'hold')
            confidence = llm_analysis.get('confidence', 0.5)
            reasoning = llm_analysis.get('reasoning', '')
            
            if confidence < 0.6:
                return {
                    "action": "hold",
                    "reason": f"Low confidence: {confidence}",
                    "llm_reasoning": reasoning
                }
            
            if recommendation in ['buy', 'sell']:
                signal = self._create_trade_signal(context, recommendation, confidence, reasoning)
                
                if signal and self.trade_executor.submit_trade_signal(signal):
                    return {
                        "action": recommendation,
                        "signal": signal.__dict__,
                        "reason": reasoning,
                        "confidence": confidence
                    }
                else:
                    return {
                        "action": "failed",
                        "reason": "Failed to submit trade signal",
                        "llm_reasoning": reasoning
                    }
            
            return {
                "action": "hold",
                "reason": reasoning,
                "confidence": confidence
            }
            
        except Exception as e:
            self.logger.error(f"Error making trading decision: {e}")
            return {"action": "error", "reason": str(e)}
    
    def _create_trade_signal(self, context: TradingContext, direction: str, confidence: float, reasoning: str) -> Optional[TradeSignal]:
        """Create a trade signal based on analysis"""
        try:
            trade_direction = TradeDirection.BUY if direction == 'buy' else TradeDirection.SELL
            
            atr_distance = context.volatility * context.current_price * 2  # 2x volatility for SL
            
            if trade_direction == TradeDirection.BUY:
                stop_loss = context.current_price - atr_distance
                take_profit = context.current_price + (atr_distance * 2)  # 2:1 RR
            else:
                stop_loss = context.current_price + atr_distance
                take_profit = context.current_price - (atr_distance * 2)
            
            risk_percent = self.risk_per_trade * confidence
            
            signal = TradeSignal(
                symbol=context.symbol,
                direction=trade_direction,
                entry_price=context.current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_percent=risk_percent,
                strategy_name="AI_LLM_Strategy",
                confidence=confidence,
                metadata={
                    "reasoning": reasoning,
                    "market_session": context.market_session,
                    "trend_direction": context.trend_direction,
                    "volatility": context.volatility
                }
            )
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error creating trade signal: {e}")
            return None
    
    def get_trading_status(self) -> Dict[str, Any]:
        """Get current trading status"""
        return {
            "is_trading_enabled": self.is_trading_enabled,
            "active_strategies": self.active_strategies,
            "last_decision_time": self.last_decision_time.isoformat(),
            "current_context": self.current_context.__dict__ if self.current_context else None,
            "trade_stats": self.trade_executor.get_trade_statistics()
        }
    
    def enable_trading(self):
        """Enable trading"""
        self.is_trading_enabled = True
        self.logger.info("Trading enabled")
    
    def disable_trading(self):
        """Disable trading"""
        self.is_trading_enabled = False
        self.logger.info("Trading disabled")
    
    def emergency_stop(self):
        """Emergency stop all trading"""
        self.disable_trading()
        self.trade_executor.emergency_stop()
        self.logger.warning("Emergency stop activated")
