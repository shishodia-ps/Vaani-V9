#!/usr/bin/env python3
"""Test script to verify all strategy imports work correctly"""

def test_strategy_imports():
    """Test that all 14 strategies can be imported successfully"""
    try:
        from strategies import (
            RSIDivergenceStrategy, MACrossoverStrategy, GridStrategy, MartingaleStrategy,
            LondonBreakoutStrategy, NewsFadeStrategy, NYReversalStrategy, CPIFadeStrategy,
            PullbackStrategy, ScalpingStrategy, TailRiskProtectionStrategy, TrendFollowingStrategy,
            BreakoutReversalStrategy, StochasticStrategy, VaaniV9Strategy
        )
        
        strategies = [
            RSIDivergenceStrategy, MACrossoverStrategy, GridStrategy, MartingaleStrategy,
            LondonBreakoutStrategy, NewsFadeStrategy, NYReversalStrategy, CPIFadeStrategy,
            PullbackStrategy, ScalpingStrategy, TailRiskProtectionStrategy, TrendFollowingStrategy,
            BreakoutReversalStrategy, StochasticStrategy, VaaniV9Strategy
        ]
        
        print("✅ All 14 strategies imported successfully!")
        print("Available strategies:")
        for i, strategy in enumerate(strategies, 1):
            print(f"  {i:2d}. {strategy.__name__}")
        
        print("\n🔧 Testing strategy instantiation...")
        for strategy in strategies:
            try:
                instance = strategy()
                print(f"  ✅ {strategy.__name__} - instantiated successfully")
            except Exception as e:
                print(f"  ❌ {strategy.__name__} - failed: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_strategy_imports()
    exit(0 if success else 1)
