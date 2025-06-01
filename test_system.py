"""
Test script to verify the forex trading bot system functionality
"""

import sys
import logging
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    
    try:
        from core.config_loader import config
        from core.broking_interface import MT5Interface
        from core.price_feed import PriceFeedManager
        from core.trade_executor import TradeExecutor
        print("✅ Core imports successful")
        
        from agents.trading_agent import TradingAgent
        from agents.llm_reasoner_agent import LLMReasonerAgent
        from agents.strategy_selector_agent import StrategySelector
        from agents.risk_agent import RiskAgent
        from agents.macro_event_agent import MacroEventAgent
        print("✅ Agent imports successful")
        
        from strategies.rsi_divergence import RSIDivergenceStrategy
        from strategies.ma_crossover import MACrossoverStrategy
        print("✅ Strategy imports successful")
        
        from ui.streamlit_dashboard import TradingDashboard
        from ui.chatbot_controller import ChatbotController
        from ui.openai_agent_backend import OpenAIAgentBackend
        print("✅ UI imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_component_initialization():
    """Test component initialization"""
    print("\nTesting component initialization...")
    
    try:
        from core.config_loader import config
        from core.broking_interface import MT5Interface
        from core.price_feed import PriceFeedManager
        from core.trade_executor import TradeExecutor
        
        mt5_interface = MT5Interface()
        print("✅ MT5Interface initialized")
        
        price_feed = PriceFeedManager(mt5_interface)
        print("✅ PriceFeedManager initialized")
        
        trade_executor = TradeExecutor(mt5_interface)
        print("✅ TradeExecutor initialized")
        
        from strategies.rsi_divergence import RSIDivergenceStrategy
        from strategies.ma_crossover import MACrossoverStrategy
        
        rsi_strategy = RSIDivergenceStrategy()
        ma_strategy = MACrossoverStrategy()
        print("✅ Trading strategies initialized")
        
        from agents.trading_agent import TradingAgent
        from agents.risk_agent import RiskAgent
        
        trading_agent = TradingAgent(trade_executor, price_feed)
        risk_agent = RiskAgent(trade_executor, config)
        print("✅ Trading agents initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False

def test_streamlit_dashboard():
    """Test Streamlit dashboard can be imported and initialized"""
    print("\nTesting Streamlit dashboard...")
    
    try:
        from ui.streamlit_dashboard import TradingDashboard
        
        dashboard = TradingDashboard()
        print("✅ TradingDashboard initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running Forex Trading Bot V9 System Tests\n")
    
    tests = [
        test_imports,
        test_component_initialization,
        test_streamlit_dashboard
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
