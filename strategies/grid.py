"""
Grid Trading Strategy
Places buy and sell orders at regular intervals above and below current price
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime

class GridStrategy:
    """Grid trading strategy implementation"""
    
    def __init__(self, 
                 grid_size: float = 0.0020,  # 20 pips for EURUSD
                 num_levels: int = 5,
                 lot_size: float = 0.01,
                 max_positions: int = 10,
                 take_profit_pips: float = 20.0,
                 stop_loss_pips: float = 100.0):
        
        self.grid_size = grid_size
        self.num_levels = num_levels
        self.lot_size = lot_size
        self.max_positions = max_positions
        self.take_profit_pips = take_profit_pips
        self.stop_loss_pips = stop_loss_pips
        
        self.logger = logging.getLogger(__name__)
        self.grid_levels = []
        self.active_orders = []
        
    def analyze(self, data: pd.DataFrame, symbol: str = "EURUSD") -> Dict[str, Any]:
        """Analyze market for grid trading opportunities"""
        try:
            if len(data) < 20:
                return self._no_signal_result("Insufficient data")
            
            current_price = data['close'].iloc[-1]
            
            returns = data['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(24)  # Daily volatility
            
            adjusted_grid_size = max(self.grid_size, volatility * 0.5)
            
            self.grid_levels = self._generate_grid_levels(current_price, adjusted_grid_size)
            
            signal = self._evaluate_grid_conditions(data, current_price)
            
            return {
                'signal': signal,
                'confidence': 0.7,
                'entry_price': current_price,
                'grid_levels': self.grid_levels,
                'adjusted_grid_size': adjusted_grid_size,
                'volatility': volatility,
                'analysis': {
                    'strategy': 'Grid Trading',
                    'current_price': current_price,
                    'grid_spacing': adjusted_grid_size,
                    'num_levels': len(self.grid_levels),
                    'market_condition': self._assess_market_condition(data)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in grid analysis: {e}")
            return self._no_signal_result(f"Analysis error: {e}")
    
    def _generate_grid_levels(self, current_price: float, grid_size: float) -> List[Dict]:
        """Generate buy and sell grid levels"""
        levels = []
        
        for i in range(1, self.num_levels + 1):
            buy_price = current_price - (grid_size * i)
            levels.append({
                'type': 'buy',
                'price': buy_price,
                'level': i,
                'distance': grid_size * i
            })
        
        for i in range(1, self.num_levels + 1):
            sell_price = current_price + (grid_size * i)
            levels.append({
                'type': 'sell',
                'price': sell_price,
                'level': i,
                'distance': grid_size * i
            })
        
        return sorted(levels, key=lambda x: x['price'])
    
    def _evaluate_grid_conditions(self, data: pd.DataFrame, current_price: float) -> str:
        """Evaluate if conditions are suitable for grid trading"""
        
        sma_20 = data['close'].rolling(20).mean().iloc[-1]
        sma_50 = data['close'].rolling(50).mean().iloc[-1] if len(data) >= 50 else sma_20
        
        price_vs_sma20 = abs(current_price - sma_20) / sma_20
        price_vs_sma50 = abs(current_price - sma_50) / sma_50
        
        returns = data['close'].pct_change().dropna()
        recent_volatility = returns.tail(20).std()
        
        if price_vs_sma20 < 0.01 and price_vs_sma50 < 0.02:  # Price near moving averages
            if 0.005 < recent_volatility < 0.02:  # Moderate volatility
                return 'GRID_SETUP'
        
        return 'HOLD'
    
    def _assess_market_condition(self, data: pd.DataFrame) -> str:
        """Assess current market condition for grid trading"""
        if len(data) < 50:
            return "Insufficient data"
        
        sma_20 = data['close'].rolling(20).mean()
        sma_50 = data['close'].rolling(50).mean()
        
        current_price = data['close'].iloc[-1]
        sma_20_current = sma_20.iloc[-1]
        sma_50_current = sma_50.iloc[-1]
        
        if current_price > sma_20_current > sma_50_current:
            return "Uptrend - Grid not ideal"
        elif current_price < sma_20_current < sma_50_current:
            return "Downtrend - Grid not ideal"
        else:
            return "Ranging - Good for grid"
    
    def calculate_position_size(self, account_balance: float, risk_percent: float = 1.0) -> float:
        """Calculate position size for grid trading"""
        risk_amount = account_balance * (risk_percent / 100)
        
        grid_risk_per_level = risk_amount / (self.num_levels * 2)  # Buy and sell levels
        
        if self.stop_loss_pips > 0:
            pip_value = 10  # For EURUSD, 1 pip = $10 for 1 lot
            max_loss_per_level = self.stop_loss_pips * pip_value
            
            if max_loss_per_level > 0:
                lot_size = grid_risk_per_level / max_loss_per_level
                return max(0.01, min(lot_size, self.lot_size))
        
        return self.lot_size
    
    def get_grid_orders(self, current_price: float) -> List[Dict]:
        """Get pending grid orders to place"""
        orders = []
        
        for level in self.grid_levels:
            if level['type'] == 'buy' and level['price'] < current_price:
                orders.append({
                    'type': 'BUY_LIMIT',
                    'price': level['price'],
                    'volume': self.lot_size,
                    'sl': level['price'] - (self.stop_loss_pips * 0.0001),
                    'tp': level['price'] + (self.take_profit_pips * 0.0001),
                    'comment': f"Grid Buy Level {level['level']}"
                })
            elif level['type'] == 'sell' and level['price'] > current_price:
                orders.append({
                    'type': 'SELL_LIMIT',
                    'price': level['price'],
                    'volume': self.lot_size,
                    'sl': level['price'] + (self.stop_loss_pips * 0.0001),
                    'tp': level['price'] - (self.take_profit_pips * 0.0001),
                    'comment': f"Grid Sell Level {level['level']}"
                })
        
        return orders
    
    def _no_signal_result(self, reason: str) -> Dict[str, Any]:
        """Return no signal result"""
        return {
            'signal': 'HOLD',
            'confidence': 0.0,
            'entry_price': 0.0,
            'reason': reason,
            'analysis': {
                'strategy': 'Grid Trading',
                'status': 'No signal',
                'reason': reason
            }
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': 'Grid Trading Strategy',
            'description': 'Places buy and sell orders at regular intervals',
            'parameters': {
                'grid_size': self.grid_size,
                'num_levels': self.num_levels,
                'lot_size': self.lot_size,
                'max_positions': self.max_positions,
                'take_profit_pips': self.take_profit_pips,
                'stop_loss_pips': self.stop_loss_pips
            },
            'market_conditions': 'Works best in ranging markets',
            'risk_level': 'Medium to High',
            'timeframe': 'Any (typically M15-H1)'
        }
