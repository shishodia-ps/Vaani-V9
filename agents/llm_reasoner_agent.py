"""
LLM-powered reasoning agent for trading decisions using OpenAI GPT-4
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

from core.config_loader import config

class LLMReasonerAgent:
    """Uses LLM to analyze market conditions and provide trading recommendations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.model = config.openai.model
        self.max_tokens = config.openai.max_tokens
        self.temperature = config.openai.temperature
        
        if AsyncOpenAI and config.openai.api_key:
            self.client = AsyncOpenAI(api_key=config.openai.api_key)
        else:
            self.logger.warning("OpenAI client not available - check API key configuration")
    
    async def analyze_trading_opportunity(self, context) -> Dict[str, Any]:
        """Analyze trading opportunity using LLM"""
        if not self.client:
            return self._fallback_analysis(context)
        
        try:
            prompt = self._create_analysis_prompt(context)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            analysis = self._parse_llm_response(content)
            
            self.logger.info(f"LLM analysis completed for {context.symbol}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in LLM analysis: {e}")
            return self._fallback_analysis(context)
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for trading analysis"""
        return """You are an expert forex trading analyst with deep knowledge of technical analysis, market psychology, and risk management. 

Your task is to analyze the provided market data and trading context to make informed trading recommendations.

Always respond in JSON format with the following structure:
{
    "recommendation": "buy|sell|hold",
    "confidence": 0.0-1.0,
    "reasoning": "detailed explanation of your analysis",
    "key_factors": ["factor1", "factor2", ...],
    "risk_assessment": "low|medium|high",
    "entry_strategy": "market|limit|stop",
    "time_horizon": "scalp|intraday|swing",
    "market_outlook": "bullish|bearish|neutral"
}

Consider:
- Technical indicators and price action
- Market session and volatility
- Support/resistance levels
- Trend direction and momentum
- Risk-reward ratio
- Current market conditions
- Economic factors

Be conservative and prioritize capital preservation. Only recommend trades with high probability setups."""
    
    def _create_analysis_prompt(self, context) -> str:
        """Create analysis prompt from trading context"""
        return f"""
Analyze the following forex trading opportunity for {context.symbol}:

CURRENT MARKET DATA:
- Symbol: {context.symbol}
- Current Price: {context.current_price}
- Market Session: {context.market_session}
- Trend Direction: {context.trend_direction}
- Volatility: {context.volatility:.4f}

SUPPORT/RESISTANCE LEVELS:
- Support: {context.support_resistance.get('support', 'N/A')}
- Resistance: {context.support_resistance.get('resistance', 'N/A')}
- Current Support: {context.support_resistance.get('current_support', 'N/A')}
- Current Resistance: {context.support_resistance.get('current_resistance', 'N/A')}

ACCOUNT STATUS:
- Account Equity: ${context.account_equity:.2f}
- Daily P&L: ${context.daily_pnl:.2f}
- Open Positions: {len(context.open_positions)}

TRADING CONTEXT:
- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
- Economic Events: {len(context.economic_events)} scheduled

Please provide your trading recommendation with detailed reasoning.
"""
    
    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        try:
            if '{' in content and '}' in content:
                start = content.find('{')
                end = content.rfind('}') + 1
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                return self._parse_text_response(content)
                
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse LLM JSON response, using text parsing")
            return self._parse_text_response(content)
    
    def _parse_text_response(self, content: str) -> Dict[str, Any]:
        """Parse text response when JSON parsing fails"""
        content_lower = content.lower()
        
        if 'buy' in content_lower and 'sell' not in content_lower:
            recommendation = 'buy'
        elif 'sell' in content_lower and 'buy' not in content_lower:
            recommendation = 'sell'
        else:
            recommendation = 'hold'
        
        confidence = 0.5  # Default
        if 'high confidence' in content_lower or 'very confident' in content_lower:
            confidence = 0.8
        elif 'low confidence' in content_lower or 'uncertain' in content_lower:
            confidence = 0.3
        elif 'medium confidence' in content_lower:
            confidence = 0.6
        
        return {
            "recommendation": recommendation,
            "confidence": confidence,
            "reasoning": content,
            "key_factors": [],
            "risk_assessment": "medium",
            "entry_strategy": "market",
            "time_horizon": "intraday",
            "market_outlook": "neutral"
        }
    
    def _fallback_analysis(self, context) -> Dict[str, Any]:
        """Fallback analysis when LLM is not available"""
        self.logger.info("Using fallback analysis (no LLM available)")
        
        recommendation = "hold"
        confidence = 0.4
        reasoning = "Fallback analysis: "
        
        if context.trend_direction == "uptrend":
            if context.current_price > context.support_resistance.get('current_support', 0):
                recommendation = "buy"
                confidence = 0.6
                reasoning += "Uptrend with price above support"
        elif context.trend_direction == "downtrend":
            if context.current_price < context.support_resistance.get('current_resistance', float('inf')):
                recommendation = "sell"
                confidence = 0.6
                reasoning += "Downtrend with price below resistance"
        else:
            reasoning += "Sideways market, no clear direction"
        
        if context.volatility > 0.03:
            confidence *= 0.7
            reasoning += ". High volatility detected"
        
        return {
            "recommendation": recommendation,
            "confidence": confidence,
            "reasoning": reasoning,
            "key_factors": ["trend_direction", "support_resistance"],
            "risk_assessment": "medium",
            "entry_strategy": "market",
            "time_horizon": "intraday",
            "market_outlook": context.trend_direction
        }
    
    async def get_market_sentiment(self, symbol: str, news_data: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze market sentiment from news and data"""
        if not self.client or not news_data:
            return {"sentiment": "neutral", "confidence": 0.5}
        
        try:
            news_text = "\n".join(news_data[:5])  # Limit to 5 news items
            
            prompt = f"""
Analyze the market sentiment for {symbol} based on the following news:

{news_text}

Provide sentiment analysis in JSON format:
{{
    "sentiment": "bullish|bearish|neutral",
    "confidence": 0.0-1.0,
    "key_themes": ["theme1", "theme2"],
    "impact_timeframe": "short|medium|long",
    "reasoning": "explanation"
}}
"""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial news sentiment analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            return self._parse_llm_response(content)
            
        except Exception as e:
            self.logger.error(f"Error in sentiment analysis: {e}")
            return {"sentiment": "neutral", "confidence": 0.5}
