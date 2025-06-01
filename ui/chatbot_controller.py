"""
Chatbot controller for handling user interactions with the trading system
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

class ChatbotController:
    """Controls chatbot interactions and command processing"""
    
    def __init__(self, trading_agent, openai_backend):
        self.trading_agent = trading_agent
        self.openai_backend = openai_backend
        self.logger = logging.getLogger(__name__)
        
        self.command_patterns = {
            'status': r'(?i)(status|how.*doing|current.*state)',
            'enable_trading': r'(?i)(enable|start|turn.*on).*trading',
            'disable_trading': r'(?i)(disable|stop|turn.*off).*trading',
            'positions': r'(?i)(position|open.*trade|current.*trade)',
            'close_all': r'(?i)(close.*all|exit.*all)',
            'strategy': r'(?i)(strategy|what.*strategy)',
            'analysis': r'(?i)(analyz|market.*condition|should.*trade)',
            'help': r'(?i)(help|command|what.*can)'
        }
    
    async def process_message(self, message: str) -> str:
        """Process user message and return response"""
        try:
            command_response = await self._process_commands(message)
            if command_response:
                return command_response
            
            if self.openai_backend and self.openai_backend.is_configured():
                context = await self._get_trading_context()
                return await self.openai_backend.chat_with_context(message, context)
            else:
                return await self._fallback_response(message)
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return f"Sorry, I encountered an error: {e}"
    
    async def _process_commands(self, message: str) -> Optional[str]:
        """Process direct commands"""
        message_lower = message.lower()
        
        if re.search(self.command_patterns['status'], message):
            return await self._get_status_response()
        
        elif re.search(self.command_patterns['enable_trading'], message):
            return await self._enable_trading()
        
        elif re.search(self.command_patterns['disable_trading'], message):
            return await self._disable_trading()
        
        elif re.search(self.command_patterns['positions'], message):
            return await self._get_positions_response()
        
        elif re.search(self.command_patterns['close_all'], message):
            return await self._close_all_positions()
        
        elif re.search(self.command_patterns['strategy'], message):
            return await self._get_strategy_response()
        
        elif re.search(self.command_patterns['analysis'], message):
            return await self._get_analysis_response()
        
        elif re.search(self.command_patterns['help'], message):
            return self._get_help_response()
        
        return None
    
    async def _get_status_response(self) -> str:
        """Get trading system status"""
        try:
            if not self.trading_agent:
                return "Trading agent not available."
            
            status = self.trading_agent.get_trading_status()
            trade_stats = self.trading_agent.trade_executor.get_trade_statistics()
            
            account_info = None
            if self.trading_agent.trade_executor.mt5_interface.connected:
                account_info = self.trading_agent.trade_executor.mt5_interface.get_account_info()
            
            response = "📊 **Trading System Status**\n\n"
            response += f"🔄 Trading Enabled: {'✅ Yes' if status['is_trading_enabled'] else '❌ No'}\n"
            response += f"📈 Active Strategy: {status.get('current_strategy', 'None')}\n"
            response += f"🎯 Total Trades: {trade_stats.get('total_trades', 0)}\n"
            response += f"📅 Daily Trades: {trade_stats.get('daily_trades', 0)}\n"
            response += f"💼 Open Positions: {trade_stats.get('open_positions', 0)}\n"
            response += f"💰 Current P&L: ${trade_stats.get('current_pnl', 0):.2f}\n"
            
            if account_info:
                response += f"💳 Account Balance: ${account_info.balance:.2f}\n"
                response += f"💎 Account Equity: ${account_info.equity:.2f}\n"
                drawdown = ((account_info.balance - account_info.equity) / account_info.balance) * 100
                response += f"📉 Current Drawdown: {abs(drawdown):.2f}%\n"
            
            if status.get('last_decision_time'):
                response += f"⏰ Last Decision: {status['last_decision_time']}\n"
            
            return response
            
        except Exception as e:
            return f"Error getting status: {e}"
    
    async def _enable_trading(self) -> str:
        """Enable trading"""
        try:
            if self.trading_agent:
                self.trading_agent.enable_trading()
                return "✅ Trading has been **enabled**. The bot will now analyze markets and execute trades."
            else:
                return "❌ Trading agent not available."
        except Exception as e:
            return f"Error enabling trading: {e}"
    
    async def _disable_trading(self) -> str:
        """Disable trading"""
        try:
            if self.trading_agent:
                self.trading_agent.disable_trading()
                return "⏹️ Trading has been **disabled**. No new trades will be executed."
            else:
                return "❌ Trading agent not available."
        except Exception as e:
            return f"Error disabling trading: {e}"
    
    async def _get_positions_response(self) -> str:
        """Get current positions"""
        try:
            if not self.trading_agent:
                return "Trading agent not available."
            
            positions = self.trading_agent.trade_executor.get_open_positions()
            
            if not positions:
                return "📭 No open positions currently."
            
            response = f"📊 **Open Positions ({len(positions)})**\n\n"
            
            for i, pos in enumerate(positions, 1):
                direction = "🟢 BUY" if pos['type'] == 0 else "🔴 SELL"
                profit_emoji = "💚" if pos['profit'] >= 0 else "💔"
                
                response += f"**{i}. {pos['symbol']}**\n"
                response += f"   {direction} | Volume: {pos['volume']}\n"
                response += f"   Entry: {pos['price_open']:.5f} | Current: {pos['price_current']:.5f}\n"
                response += f"   {profit_emoji} P&L: ${pos['profit']:.2f}\n"
                if pos['comment']:
                    response += f"   Comment: {pos['comment']}\n"
                response += "\n"
            
            return response
            
        except Exception as e:
            return f"Error getting positions: {e}"
    
    async def _close_all_positions(self) -> str:
        """Close all open positions"""
        try:
            if not self.trading_agent:
                return "Trading agent not available."
            
            closed_count = self.trading_agent.trade_executor.close_all_positions()
            
            if closed_count > 0:
                return f"✅ Successfully closed **{closed_count}** positions."
            else:
                return "ℹ️ No positions were open to close."
                
        except Exception as e:
            return f"Error closing positions: {e}"
    
    async def _get_strategy_response(self) -> str:
        """Get current strategy information"""
        try:
            if not self.trading_agent:
                return "Trading agent not available."
            
            status = self.trading_agent.get_trading_status()
            
            response = "🎯 **Current Trading Strategy**\n\n"
            response += f"Strategy: **AI_LLM_Strategy**\n"
            response += f"Active Strategies: {', '.join(status.get('active_strategies', ['None']))}\n\n"
            
            if status.get('current_context'):
                context = status['current_context']
                response += "📊 **Market Context:**\n"
                response += f"• Symbol: {context.get('symbol', 'N/A')}\n"
                response += f"• Trend: {context.get('trend_direction', 'N/A')}\n"
                response += f"• Session: {context.get('market_session', 'N/A')}\n"
                response += f"• Volatility: {context.get('volatility', 0):.4f}\n"
            
            response += "\n🤖 The AI strategy uses GPT-4 to analyze market conditions, "
            response += "technical indicators, and economic factors to make trading decisions."
            
            return response
            
        except Exception as e:
            return f"Error getting strategy info: {e}"
    
    async def _get_analysis_response(self) -> str:
        """Get market analysis"""
        try:
            if not self.trading_agent:
                return "Trading agent not available."
            
            analysis = await self.trading_agent.analyze_market_and_trade("EURUSD")
            
            response = "📈 **Market Analysis**\n\n"
            
            if analysis.get('status') == 'decision_made':
                decision = analysis.get('decision', {})
                llm_analysis = analysis.get('llm_analysis', {})
                
                response += f"🎯 **Recommendation:** {decision.get('action', 'N/A').upper()}\n"
                response += f"🎲 **Confidence:** {llm_analysis.get('confidence', 0):.2f}\n"
                response += f"⚖️ **Risk Assessment:** {llm_analysis.get('risk_assessment', 'N/A')}\n"
                response += f"⏰ **Time Horizon:** {llm_analysis.get('time_horizon', 'N/A')}\n"
                response += f"📊 **Market Outlook:** {llm_analysis.get('market_outlook', 'N/A')}\n\n"
                
                if llm_analysis.get('reasoning'):
                    response += f"💭 **Analysis:**\n{llm_analysis['reasoning']}\n\n"
                
                if llm_analysis.get('key_factors'):
                    response += f"🔑 **Key Factors:** {', '.join(llm_analysis['key_factors'])}\n"
                
            elif analysis.get('status') == 'no_trade':
                response += "⏸️ **No trading opportunity identified**\n"
                response += "Current market conditions don't meet trading criteria.\n"
                
            elif analysis.get('status') == 'waiting':
                response += "⏳ **Analysis in cooldown**\n"
                response += "Waiting for next analysis cycle.\n"
                
            else:
                response += f"❌ **Analysis Status:** {analysis.get('status', 'Unknown')}\n"
                if analysis.get('message'):
                    response += f"Message: {analysis['message']}\n"
            
            return response
            
        except Exception as e:
            return f"Error getting analysis: {e}"
    
    def _get_help_response(self) -> str:
        """Get help information"""
        return """🤖 **Trading Bot Commands**

**Status & Information:**
• "status" - Get current trading system status
• "positions" - Show open positions
• "strategy" - Current strategy information
• "analysis" - Get market analysis

**Trading Controls:**
• "enable trading" - Start automated trading
• "disable trading" - Stop automated trading
• "close all" - Close all open positions

**General:**
• "help" - Show this help message

**Natural Language:**
You can also ask questions in natural language like:
• "How is the bot performing today?"
• "What's the current market condition?"
• "Should I be worried about my positions?"
• "Explain the current strategy"

The bot uses GPT-4 to understand and respond to your questions about trading, market analysis, and system status."""
    
    async def _get_trading_context(self) -> Dict[str, Any]:
        """Get current trading context for OpenAI"""
        context = {
            "timestamp": datetime.now().isoformat(),
            "trading_enabled": False,
            "positions": [],
            "account_info": None,
            "trade_stats": {}
        }
        
        try:
            if self.trading_agent:
                status = self.trading_agent.get_trading_status()
                context["trading_enabled"] = status.get("is_trading_enabled", False)
                context["current_context"] = status.get("current_context")
                
                positions = self.trading_agent.trade_executor.get_open_positions()
                context["positions"] = positions
                
                trade_stats = self.trading_agent.trade_executor.get_trade_statistics()
                context["trade_stats"] = trade_stats
                
                if self.trading_agent.trade_executor.mt5_interface.connected:
                    account_info = self.trading_agent.trade_executor.mt5_interface.get_account_info()
                    if account_info:
                        context["account_info"] = {
                            "balance": account_info.balance,
                            "equity": account_info.equity,
                            "margin": account_info.margin,
                            "free_margin": account_info.free_margin
                        }
        
        except Exception as e:
            self.logger.error(f"Error getting trading context: {e}")
        
        return context
    
    async def _fallback_response(self, message: str) -> str:
        """Fallback response when OpenAI is not available"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['hello', 'hi', 'hey']):
            return "Hello! I'm your forex trading bot. Type 'help' to see available commands."
        
        elif any(word in message_lower for word in ['thank', 'thanks']):
            return "You're welcome! Let me know if you need anything else."
        
        elif any(word in message_lower for word in ['bye', 'goodbye']):
            return "Goodbye! Happy trading!"
        
        else:
            return ("I'm not sure how to respond to that. Please configure your OpenAI API key "
                   "for full conversational capabilities, or type 'help' for available commands.")
