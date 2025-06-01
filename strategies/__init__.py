"""
Strategies package for the forex trading bot
Contains all trading strategy implementations
"""

from .rsi_divergence import RSIDivergenceStrategy
from .ma_crossover import MACrossoverStrategy

__all__ = [
    'RSIDivergenceStrategy',
    'MACrossoverStrategy'
]
