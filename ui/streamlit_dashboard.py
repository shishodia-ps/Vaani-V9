"""
Main Streamlit dashboard for the forex trading bot
Provides comprehensive UI with multiple tabs for monitoring and control
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config_loader import config, ConfigLoader
from core.broking_interface import MT5Interface
from core.price_feed import PriceFeedManager
from core.trade_executor import TradeExecutor
from agents.trading_agent import TradingAgent
from ui.chatbot_controller import ChatbotController
from ui.openai_agent_backend import OpenAIAgentBackend

st.set_page_config(
    page_title="Forex Trading Bot V9",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-online { background-color: #28a745; }
    .status-offline { background-color: #dc3545; }
    .status-warning { background-color: #ffc107; }
</style>
""", unsafe_allow_html=True)

class TradingDashboard:
    """Main trading dashboard class"""
    
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.mt5_interface = None
        self.price_feed = None
        self.trade_executor = None
        self.trading_agent = None
        self.chatbot_controller = None
        self.openai_backend = None
        
        self._initialize_session_state()
        
        self._initialize_components()
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'trading_enabled' not in st.session_state:
            st.session_state.trading_enabled = False
        
        if 'mt5_connected' not in st.session_state:
            st.session_state.mt5_connected = False
        
        if 'openai_configured' not in st.session_state:
            st.session_state.openai_configured = bool(config.openai.api_key)
        
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'current_strategy' not in st.session_state:
            st.session_state.current_strategy = "AI_LLM_Strategy"
        
        if 'trade_log' not in st.session_state:
            st.session_state.trade_log = []
    
    def _initialize_components(self):
        """Initialize trading system components"""
        try:
            self.mt5_interface = MT5Interface(
                login=config.mt5.login,
                password=config.mt5.password,
                server=config.mt5.server,
                path=config.mt5.path
            )
            
            self.price_feed = PriceFeedManager(self.mt5_interface)
            
            self.trade_executor = TradeExecutor(self.mt5_interface)
            
            self.trading_agent = TradingAgent(self.trade_executor, self.price_feed)
            
            self.openai_backend = OpenAIAgentBackend()
            self.chatbot_controller = ChatbotController(
                self.trading_agent, 
                self.openai_backend
            )
            
        except Exception as e:
            st.error(f"Error initializing components: {e}")
    
    def run(self):
        """Main dashboard entry point"""
        st.markdown('<h1 class="main-header">🤖 Forex Trading Bot V9</h1>', unsafe_allow_html=True)
        
        self._render_sidebar()
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Strategy Monitor", 
            "📈 Analytics", 
            "💰 Capital Tracker", 
            "💬 Chat", 
            "📋 Log Viewer"
        ])
        
        with tab1:
            self._render_strategy_monitor()
        
        with tab2:
            self._render_analytics()
        
        with tab3:
            self._render_capital_tracker()
        
        with tab4:
            self._render_chat_interface()
        
        with tab5:
            self._render_log_viewer()
    
    def _render_sidebar(self):
        """Render sidebar with configuration and controls"""
        st.sidebar.header("🔧 Configuration")
        
        st.sidebar.subheader("Connection Status")
        
        mt5_status = "🟢 Connected" if st.session_state.mt5_connected else "🔴 Disconnected"
        st.sidebar.write(f"MT5: {mt5_status}")
        
        if st.sidebar.button("Connect to MT5"):
            if self.mt5_interface and self.mt5_interface.connect():
                st.session_state.mt5_connected = True
                st.sidebar.success("MT5 Connected!")
            else:
                st.sidebar.error("MT5 Connection Failed")
        
        st.sidebar.subheader("OpenAI Configuration")
        
        openai_key = st.sidebar.text_input(
            "OpenAI API Key", 
            value=config.openai.api_key or "",
            type="password",
            help="Enter your OpenAI API key for GPT-4 analysis"
        )
        
        if openai_key and openai_key != config.openai.api_key:
            config.openai.api_key = openai_key
            st.session_state.openai_configured = True
            if self.openai_backend:
                self.openai_backend.update_api_key(openai_key)
            st.sidebar.success("OpenAI API Key Updated!")
        
        st.sidebar.subheader("Trading Controls")
        
        trading_enabled = st.sidebar.toggle(
            "Enable Trading", 
            value=st.session_state.trading_enabled
        )
        
        if trading_enabled != st.session_state.trading_enabled:
            st.session_state.trading_enabled = trading_enabled
            if self.trading_agent:
                if trading_enabled:
                    self.trading_agent.enable_trading()
                else:
                    self.trading_agent.disable_trading()
        
        if st.sidebar.button("🚨 Emergency Stop", type="primary"):
            if self.trading_agent:
                self.trading_agent.emergency_stop()
            st.sidebar.warning("Emergency stop activated!")
        
        st.sidebar.subheader("Risk Settings")
        
        risk_percent = st.sidebar.slider(
            "Risk per Trade (%)", 
            min_value=0.1, 
            max_value=5.0, 
            value=config.trading.default_risk_percent,
            step=0.1
        )
        
        max_drawdown = st.sidebar.slider(
            "Max Drawdown (%)", 
            min_value=1.0, 
            max_value=20.0, 
            value=config.trading.max_drawdown_percent,
            step=0.5
        )
        
        symbol = st.sidebar.selectbox(
            "Trading Symbol",
            ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"],
            index=0
        )
    
    def _render_strategy_monitor(self):
        """Render strategy monitoring tab"""
        st.header("📊 Strategy Monitor")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.subheader("Current Strategy")
            st.info(f"**{st.session_state.current_strategy}**")
            
            if self.trading_agent:
                status = self.trading_agent.get_trading_status()
                if status.get('current_context'):
                    context = status['current_context']
                    st.write(f"**Symbol:** {context.get('symbol', 'N/A')}")
                    st.write(f"**Trend:** {context.get('trend_direction', 'N/A')}")
                    st.write(f"**Session:** {context.get('market_session', 'N/A')}")
                    st.write(f"**Volatility:** {context.get('volatility', 0):.4f}")
        
        with col2:
            st.metric("Trading Status", "🟢 Active" if st.session_state.trading_enabled else "🔴 Inactive")
        
        with col3:
            if st.button("🔄 Refresh Strategy"):
                st.rerun()
        
        st.subheader("Real-time Prices")
        
        if self.price_feed and st.session_state.mt5_connected:
            price_data = self._get_current_prices()
            if price_data:
                df = pd.DataFrame(price_data)
                st.dataframe(df, use_container_width=True)
        else:
            st.warning("Connect to MT5 to view real-time prices")
        
        st.subheader("Strategy Performance")
        
        if self.trade_executor:
            stats = self.trade_executor.get_trade_statistics()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Trades", stats.get('total_trades', 0))
            
            with col2:
                st.metric("Daily Trades", stats.get('daily_trades', 0))
            
            with col3:
                st.metric("Open Positions", stats.get('open_positions', 0))
            
            with col4:
                st.metric("Current P&L", f"${stats.get('current_pnl', 0):.2f}")
    
    def _render_analytics(self):
        """Render analytics tab with charts and technical analysis"""
        st.header("📈 Analytics")
        
        symbol = st.selectbox("Select Symbol for Analysis", ["EURUSD", "GBPUSD", "USDJPY"])
        timeframe = st.selectbox("Timeframe", ["M15", "H1", "H4", "D1"])
        
        if self.price_feed:
            df = self.price_feed.get_historical_data(symbol, timeframe, 200)
            
            if df is not None and not df.empty:
                df = self.price_feed.calculate_technical_indicators(df)
                
                fig = self._create_price_chart(df, symbol, timeframe)
                st.plotly_chart(fig, use_container_width=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Technical Indicators")
                    if not df.empty:
                        latest = df.iloc[-1]
                        st.write(f"**RSI:** {latest.get('rsi', 0):.2f}")
                        st.write(f"**MACD:** {latest.get('macd', 0):.5f}")
                        st.write(f"**ATR:** {latest.get('atr', 0):.5f}")
                        st.write(f"**SMA 20:** {latest.get('sma_20', 0):.5f}")
                        st.write(f"**SMA 50:** {latest.get('sma_50', 0):.5f}")
                
                with col2:
                    st.subheader("Market Analysis")
                    volatility_metrics = self.price_feed.get_volatility_metrics(symbol)
                    
                    for key, value in volatility_metrics.items():
                        st.write(f"**{key.replace('_', ' ').title()}:** {value:.4f}")
            else:
                st.warning("No historical data available")
    
    def _render_capital_tracker(self):
        """Render capital tracking and risk management tab"""
        st.header("💰 Capital Tracker")
        
        if self.mt5_interface and st.session_state.mt5_connected:
            account_info = self.mt5_interface.get_account_info()
            
            if account_info:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Balance", f"${account_info.balance:.2f}")
                
                with col2:
                    st.metric("Equity", f"${account_info.equity:.2f}")
                
                with col3:
                    st.metric("Free Margin", f"${account_info.free_margin:.2f}")
                
                with col4:
                    margin_level = account_info.margin_level if account_info.margin_level else 0
                    st.metric("Margin Level", f"{margin_level:.2f}%")
                
                drawdown = ((account_info.balance - account_info.equity) / account_info.balance) * 100
                
                st.subheader("Risk Indicators")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_dd = go.Figure(go.Indicator(
                        mode = "gauge+number+delta",
                        value = abs(drawdown),
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "Current Drawdown (%)"},
                        delta = {'reference': config.trading.max_drawdown_percent},
                        gauge = {
                            'axis': {'range': [None, 20]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 5], 'color': "lightgray"},
                                {'range': [5, 10], 'color': "yellow"},
                                {'range': [10, 20], 'color': "red"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': config.trading.max_drawdown_percent
                            }
                        }
                    ))
                    fig_dd.update_layout(height=300)
                    st.plotly_chart(fig_dd, use_container_width=True)
                
                with col2:
                    if self.trade_executor:
                        positions = self.trade_executor.get_open_positions()
                        if positions:
                            pnl_data = [pos['profit'] for pos in positions]
                            symbols = [pos['symbol'] for pos in positions]
                            
                            fig_pnl = px.bar(
                                x=symbols, 
                                y=pnl_data,
                                title="Open Positions P&L",
                                color=pnl_data,
                                color_continuous_scale="RdYlGn"
                            )
                            st.plotly_chart(fig_pnl, use_container_width=True)
                        else:
                            st.info("No open positions")
                
                st.subheader("Position Management")
                
                if self.trade_executor:
                    positions = self.trade_executor.get_open_positions()
                    
                    if positions:
                        df_positions = pd.DataFrame(positions)
                        st.dataframe(df_positions, use_container_width=True)
                        
                        if st.button("Close All Positions"):
                            closed_count = self.trade_executor.close_all_positions()
                            st.success(f"Closed {closed_count} positions")
                    else:
                        st.info("No open positions")
            else:
                st.error("Unable to retrieve account information")
        else:
            st.warning("Connect to MT5 to view account information")
    
    def _render_chat_interface(self):
        """Render chat interface for interacting with the trading bot"""
        st.header("💬 Chat with Trading Bot")
        
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.chat_message("user").write(message['content'])
                else:
                    st.chat_message("assistant").write(message['content'])
        
        if prompt := st.chat_input("Ask about trading status, strategies, or give commands..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            st.chat_message("user").write(prompt)
            
            if self.chatbot_controller:
                try:
                    response = asyncio.run(self.chatbot_controller.process_message(prompt))
                    
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    
                    st.chat_message("assistant").write(response)
                    
                except Exception as e:
                    error_msg = f"Error processing message: {e}"
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
                    st.chat_message("assistant").write(error_msg)
            else:
                fallback_msg = "Chatbot not available. Please configure OpenAI API key."
                st.session_state.chat_history.append({"role": "assistant", "content": fallback_msg})
                st.chat_message("assistant").write(fallback_msg)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Clear Chat History"):
                st.session_state.chat_history = []
                st.rerun()
        
        with col2:
            if st.button("Export Chat"):
                chat_export = json.dumps(st.session_state.chat_history, indent=2)
                st.download_button(
                    "Download Chat History",
                    chat_export,
                    file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    def _render_log_viewer(self):
        """Render log viewer tab"""
        st.header("📋 Log Viewer")
        
        log_level = st.selectbox("Log Level", ["ALL", "INFO", "WARNING", "ERROR"])
        
        st.subheader("Trade Log")
        
        if self.trade_executor:
            trades = self.trade_executor.executed_trades
            
            if trades:
                trade_data = []
                for trade in trades:
                    trade_data.append({
                        "Time": trade.execution_time or trade.signal.timestamp,
                        "Symbol": trade.signal.symbol,
                        "Direction": trade.signal.direction.value,
                        "Volume": trade.volume,
                        "Price": trade.executed_price,
                        "Status": trade.status.value,
                        "Strategy": trade.signal.strategy_name
                    })
                
                df_trades = pd.DataFrame(trade_data)
                st.dataframe(df_trades, use_container_width=True)
            else:
                st.info("No trades executed yet")
        
        st.subheader("System Logs")
        
        try:
            log_file_path = "data/logs/trading_bot.log"
            if os.path.exists(log_file_path):
                with open(log_file_path, 'r') as f:
                    logs = f.readlines()
                
                if log_level != "ALL":
                    logs = [log for log in logs if log_level in log]
                
                recent_logs = logs[-100:]  # Last 100 lines
                log_text = "".join(recent_logs)
                st.text_area("Recent Logs", log_text, height=400)
            else:
                st.info("No log file found")
        except Exception as e:
            st.error(f"Error reading logs: {e}")
    
    def _get_current_prices(self) -> List[Dict]:
        """Get current prices for display"""
        symbols = ["EURUSD", "GBPUSD", "USDJPY"]
        price_data = []
        
        for symbol in symbols:
            tick = self.price_feed.get_current_price(symbol) if self.price_feed else None
            if tick:
                price_data.append({
                    "Symbol": symbol,
                    "Bid": f"{tick.bid:.5f}",
                    "Ask": f"{tick.ask:.5f}",
                    "Spread": f"{tick.spread:.5f}",
                    "Time": tick.timestamp.strftime("%H:%M:%S")
                })
        
        return price_data
    
    def _create_price_chart(self, df: pd.DataFrame, symbol: str, timeframe: str):
        """Create price chart with technical indicators"""
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=(f'{symbol} {timeframe} Price', 'RSI', 'MACD'),
            row_heights=[0.6, 0.2, 0.2]
        )
        
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Price'
            ),
            row=1, col=1
        )
        
        if 'sma_20' in df.columns:
            fig.add_trace(
                go.Scatter(x=df.index, y=df['sma_20'], name='SMA 20', line=dict(color='orange')),
                row=1, col=1
            )
        
        if 'sma_50' in df.columns:
            fig.add_trace(
                go.Scatter(x=df.index, y=df['sma_50'], name='SMA 50', line=dict(color='blue')),
                row=1, col=1
            )
        
        if 'rsi' in df.columns:
            fig.add_trace(
                go.Scatter(x=df.index, y=df['rsi'], name='RSI', line=dict(color='purple')),
                row=2, col=1
            )
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        if 'macd' in df.columns:
            fig.add_trace(
                go.Scatter(x=df.index, y=df['macd'], name='MACD', line=dict(color='blue')),
                row=3, col=1
            )
            if 'macd_signal' in df.columns:
                fig.add_trace(
                    go.Scatter(x=df.index, y=df['macd_signal'], name='Signal', line=dict(color='red')),
                    row=3, col=1
                )
        
        fig.update_layout(
            title=f'{symbol} Technical Analysis',
            xaxis_rangeslider_visible=False,
            height=800
        )
        
        return fig

def main():
    """Main entry point for Streamlit dashboard"""
    dashboard = TradingDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()
