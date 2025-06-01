"""
OpenAI agent backend for handling GPT-4 conversations and analysis
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

from core.config_loader import config

class OpenAIAgentBackend:
    """Backend for OpenAI GPT-4 integration"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.api_key = config.openai.api_key
        self.model = config.openai.model
        self.max_tokens = config.openai.max_tokens
        self.temperature = config.openai.temperature

        if AsyncOpenAI and self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.logger.warning("OpenAI client not available - check API key configuration")

    def is_configured(self) -> bool:
        """Check if OpenAI is properly configured"""
        return self.client is not None

    def update_api_key(self, api_key: str):
        """Update OpenAI API key"""
        self.api_key = api_key
        if AsyncOpenAI and api_key:
            self.client = AsyncOpenAI(api_key=api_key)
            self.logger.info("OpenAI API key updated")
        else:
            self.client = None
            self.logger.warning("Invalid API key or OpenAI not available")

    async def chat_with_context(self, message: str, context: Dict[str, Any]) -> str:
        """Chat with GPT-4 using trading context"""
        if not self.client:
            return "OpenAI not configured. Please set your API key."

        try:
            system_prompt = self._create_system_prompt(context)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"Error in OpenAI chat: {e}")
            return f"Sorry, I encountered an error: {e}"

    def _create_system_prompt(self, context: Dict[str, Any]) -> str:
        """Create system prompt with trading context"""
        prompt = """You are an expert forex trading assistant and analyst. You help users understand their trading system, analyze market conditions, and provide insights about their trading performance.

Current Trading Context:
"""

        prompt += f"- Current Time: {context.get('timestamp', 'Unknown')}\n"

        prompt += f"- Trading Enabled: {context.get('trading_enabled', False)}\n"

        if context.get('account_info'):
            account = context['account_info']
            prompt += f"- Account Balance: ${account.get('balance', 0):.2f}\n"
            prompt += f"- Account Equity: ${account.get('equity', 0):.2f}\n"
            prompt += f"- Free Margin: ${account.get('free_margin', 0):.2f}\n"

        positions = context.get('positions', [])
        prompt += f"- Open Positions: {len(positions)}\n"

        if positions:
            prompt += "- Position Details:\n"
            for pos in positions[:5]:  # Limit to 5 positions
                direction = "BUY" if pos.get('type') == 0 else "SELL"
                prompt += f"  * {pos.get('symbol')}: {direction} {pos.get('volume')} lots, P&L: ${pos.get('profit', 0):.2f}\n"

        trade_stats = context.get('trade_stats', {})
        prompt += f"- Total Trades Today: {trade_stats.get('daily_trades', 0)}\n"
        prompt += f"- Current P&L: ${trade_stats.get('current_pnl', 0):.2f}\n"

        if context.get('current_context'):
            market_ctx = context['current_context']
            prompt += f"- Current Symbol: {market_ctx.get('symbol', 'N/A')}\n"
            prompt += f"- Market Trend: {market_ctx.get('trend_direction', 'N/A')}\n"
            prompt += f"- Market Session: {market_ctx.get('market_session', 'N/A')}\n"
            prompt += f"- Volatility: {market_ctx.get('volatility', 0):.4f}\n"

        prompt += """
Your role:
1. Answer questions about the trading system, performance, and market conditions
2. Provide insights and analysis based on the current context
3. Help users understand their trading results and market opportunities
4. Explain trading concepts and strategies in simple terms
5. Give advice on risk management and trading best practices

Guidelines:
- Be helpful, informative, and professional
- Use the provided context to give specific, relevant answers
- If asked about specific trades or positions, refer to the actual data
- Provide educational content when appropriate
- Always emphasize risk management and responsible trading
- If you don't have enough information, ask for clarification

Respond in a conversational, helpful manner while being accurate and informative.
"""

        return prompt

    async def analyze_market_sentiment(self, news_data: List[str], symbol: str = "EURUSD") -> Dict[str, Any]:
        """Analyze market sentiment from news data"""
        if not self.client or not news_data:
            return {"sentiment": "neutral", "confidence": 0.5}

        try:
            news_text = "\n".join(news_data[:5])  # Limit to 5 news items

            prompt = f"""
Analyze the market sentiment for {symbol} based on the following recent news:

{news_text}

Provide a JSON response with sentiment analysis:
{{
    "sentiment": "bullish|bearish|neutral",
    "confidence": 0.0-1.0,
    "key_themes": ["theme1", "theme2"],
    "impact_timeframe": "short|medium|long",
    "reasoning": "detailed explanation",
    "trading_implications": "how this might affect {symbol} trading"
}}
"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial news sentiment analyst specializing in forex markets."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )

            content = response.choices[0].message.content

            try:
                if '{' in content and '}' in content:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    json_str = content[start:end]
                    return json.loads(json_str)
            except json.JSONDecodeError:
                pass

            return self._parse_sentiment_text(content)

        except Exception as e:
            self.logger.error(f"Error in sentiment analysis: {e}")
            return {"sentiment": "neutral", "confidence": 0.5, "error": str(e)}

    def _parse_sentiment_text(self, content: str) -> Dict[str, Any]:
        """Parse sentiment from text when JSON parsing fails"""
        content_lower = content.lower()

        if 'bullish' in content_lower or 'positive' in content_lower:
            sentiment = 'bullish'
        elif 'bearish' in content_lower or 'negative' in content_lower:
            sentiment = 'bearish'
        else:
            sentiment = 'neutral'

        confidence = 0.5
        if 'high confidence' in content_lower or 'very confident' in content_lower:
            confidence = 0.8
        elif 'low confidence' in content_lower or 'uncertain' in content_lower:
            confidence = 0.3

        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "reasoning": content,
            "key_themes": [],
            "impact_timeframe": "medium",
            "trading_implications": "Monitor for trading opportunities"
        }

    async def get_trading_advice(self, question: str, context: Dict[str, Any]) -> str:
        """Get specific trading advice"""
        if not self.client:
            return "OpenAI not configured for trading advice."

        try:
            system_prompt = """You are an expert forex trading advisor. Provide specific, actionable trading advice based on the user's question and current trading context.

Focus on:
- Risk management principles
- Market analysis techniques
- Trading psychology
- Practical strategies
- Position sizing and money management

Always emphasize responsible trading and risk management."""

            context_summary = self._summarize_context(context)

            full_prompt = f"""
Trading Context:
{context_summary}

User Question: {question}

Please provide specific, helpful trading advice based on the current situation.
"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"Error getting trading advice: {e}")
            return f"Error getting advice: {e}"

    def _summarize_context(self, context: Dict[str, Any]) -> str:
        """Summarize trading context for prompts"""
        summary = []

        if context.get('trading_enabled'):
            summary.append("Trading is currently enabled")
        else:
            summary.append("Trading is currently disabled")

        if context.get('account_info'):
            account = context['account_info']
            summary.append(f"Account balance: ${account.get('balance', 0):.2f}")
            summary.append(f"Account equity: ${account.get('equity', 0):.2f}")

        positions = context.get('positions', [])
        summary.append(f"Open positions: {len(positions)}")

        trade_stats = context.get('trade_stats', {})
        summary.append(f"Daily trades: {trade_stats.get('daily_trades', 0)}")
        summary.append(f"Current P&L: ${trade_stats.get('current_pnl', 0):.2f}")

        return "\n".join(summary)
