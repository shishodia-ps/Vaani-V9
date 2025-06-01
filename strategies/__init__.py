"""
Strategies package for the forex trading bot
Contains all trading strategy implementations
"""

from .rsi_divergence import RSIDivergenceStrategy
from .ma_crossover import MACrossoverStrategy
from .grid import GridStrategy
from .martingale import MartingaleStrategy
from .london_breakout import LondonBreakoutStrategy
from .news_fade import NewsFadeStrategy
from .ny_reversal import NYReversalStrategy
from .cpi_fade import CPIFadeStrategy
from .pullback import PullbackStrategy
from .scalping import ScalpingStrategy
from .tail_risk_protection import TailRiskProtectionStrategy
from .trend_following import TrendFollowingStrategy
from .breakout_reversal import BreakoutReversalStrategy
from .stochastic import StochasticStrategy
from .vaani_v9 import VaaniV9Strategy

__all__ = [
    'RSIDivergenceStrategy',
    'MACrossoverStrategy',
    'GridStrategy',
    'MartingaleStrategy',
    'LondonBreakoutStrategy',
    'NewsFadeStrategy',
    'NYReversalStrategy',
    'CPIFadeStrategy',
    'PullbackStrategy',
    'ScalpingStrategy',
    'TailRiskProtectionStrategy',
    'TrendFollowingStrategy',
    'BreakoutReversalStrategy',
    'StochasticStrategy',
    'VaaniV9Strategy'
]
