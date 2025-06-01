"""
Core package for the forex trading bot
Contains fundamental trading system components
"""

from .config_loader import ConfigLoader, config
from .broking_interface import MT5Interface
from .price_feed import PriceFeedManager
from .trade_executor import TradeExecutor

__all__ = [
    'ConfigLoader',
    'config',
    'MT5Interface',
    'PriceFeedManager', 
    'TradeExecutor'
]
