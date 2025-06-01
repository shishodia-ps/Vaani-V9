"""
Advanced Backtesting Engine for VaaniV9 Strategy
Provides comprehensive backtesting and validation capabilities
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

@dataclass
class BacktestResult:
    """Backtest result data structure"""
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    avg_trade_duration: float
    profit_factor: float
    calmar_ratio: float
    sortino_ratio: float
    var_95: float
    trades: List[Dict]
    equity_curve: pd.Series
    monthly_returns: pd.Series

class BacktestingEngine:
    """Advanced backtesting engine for strategy validation"""
    
    def __init__(self, initial_capital: float = 10000.0, commission: float = 0.0001):
        self.initial_capital = initial_capital
        self.commission = commission
        self.logger = logging.getLogger(__name__)
        
    def run_backtest(self, strategy, data: pd.DataFrame, 
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None) -> BacktestResult:
        """Run comprehensive backtest on strategy"""
        try:
            if start_date:
                data = data[data.index >= start_date]
            if end_date:
                data = data[data.index <= end_date]
            
            if len(data) < 100:
                raise ValueError("Insufficient data for backtesting (minimum 100 candles required)")
            
            capital = self.initial_capital
            position = 0.0
            trades = []
            equity_curve = []
            
            for i in range(100, len(data)):  # Start after 100 candles for proper analysis
                current_data = data.iloc[:i+1]
                
                signal_result = strategy.analyze(current_data)
                signal = signal_result.get('signal', 'HOLD')
                confidence = signal_result.get('confidence', 0.0)
                
                current_price = current_data['close'].iloc[-1]
                timestamp = current_data.index[-1]
                
                if signal == 'BUY' and position <= 0 and confidence > 0.6:
                    if position < 0:
                        pnl = -position * (current_price - entry_price) - abs(position) * current_price * self.commission
                        capital += pnl
                        trades.append({
                            'entry_time': entry_time,
                            'exit_time': timestamp,
                            'entry_price': entry_price,
                            'exit_price': current_price,
                            'position_size': position,
                            'pnl': pnl,
                            'type': 'SHORT'
                        })
                    
                    position_size = self._calculate_position_size(capital, current_price, signal_result)
                    position = position_size
                    entry_price = current_price
                    entry_time = timestamp
                    
                elif signal == 'SELL' and position >= 0 and confidence > 0.6:
                    if position > 0:
                        pnl = position * (current_price - entry_price) - position * current_price * self.commission
                        capital += pnl
                        trades.append({
                            'entry_time': entry_time,
                            'exit_time': timestamp,
                            'entry_price': entry_price,
                            'exit_price': current_price,
                            'position_size': position,
                            'pnl': pnl,
                            'type': 'LONG'
                        })
                    
                    position_size = self._calculate_position_size(capital, current_price, signal_result)
                    position = -position_size
                    entry_price = current_price
                    entry_time = timestamp
                
                if position != 0:
                    unrealized_pnl = position * (current_price - entry_price)
                    current_equity = capital + unrealized_pnl
                else:
                    current_equity = capital
                
                equity_curve.append(current_equity)
            
            if position != 0:
                final_price = data['close'].iloc[-1]
                final_pnl = position * (final_price - entry_price) - abs(position) * final_price * self.commission
                capital += final_pnl
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': data.index[-1],
                    'entry_price': entry_price,
                    'exit_price': final_price,
                    'position_size': position,
                    'pnl': final_pnl,
                    'type': 'LONG' if position > 0 else 'SHORT'
                })
            
            return self._calculate_performance_metrics(trades, equity_curve, data.index[-len(equity_curve):])
            
        except Exception as e:
            self.logger.error(f"Backtest error: {e}")
            raise
    
    def _calculate_position_size(self, capital: float, price: float, signal_result: Dict) -> float:
        """Calculate position size based on capital and risk"""
        risk_per_trade = 0.02  # 2% risk per trade
        confidence = signal_result.get('confidence', 0.5)
        
        base_size = (capital * risk_per_trade) / price
        adjusted_size = base_size * confidence
        
        return min(adjusted_size, capital * 0.1 / price)  # Max 10% of capital per trade
    
    def _calculate_performance_metrics(self, trades: List[Dict], 
                                     equity_curve: List[float], 
                                     dates: pd.Index) -> BacktestResult:
        """Calculate comprehensive performance metrics"""
        
        if not trades:
            return BacktestResult(
                total_return=0.0, sharpe_ratio=0.0, max_drawdown=0.0,
                win_rate=0.0, total_trades=0, avg_trade_duration=0.0,
                profit_factor=0.0, calmar_ratio=0.0, sortino_ratio=0.0,
                var_95=0.0, trades=[], equity_curve=pd.Series(),
                monthly_returns=pd.Series()
            )
        
        equity_series = pd.Series(equity_curve, index=dates)
        
        total_return = (equity_curve[-1] - self.initial_capital) / self.initial_capital
        
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] < 0]
        
        win_rate = len(winning_trades) / len(trades) if trades else 0
        
        gross_profit = sum(t['pnl'] for t in winning_trades)
        gross_loss = abs(sum(t['pnl'] for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max
        max_drawdown = abs(drawdown.min())
        
        returns = equity_series.pct_change().dropna()
        
        if returns.std() > 0:
            sharpe_ratio = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
        else:
            sharpe_ratio = 0.0
        
        negative_returns = returns[returns < 0]
        if len(negative_returns) > 0 and negative_returns.std() > 0:
            sortino_ratio = (returns.mean() * 252) / (negative_returns.std() * np.sqrt(252))
        else:
            sortino_ratio = 0.0
        
        calmar_ratio = (total_return * 100) / (max_drawdown * 100) if max_drawdown > 0 else 0.0
        
        var_95 = returns.quantile(0.05) if len(returns) > 0 else 0.0
        
        trade_durations = []
        for trade in trades:
            if 'entry_time' in trade and 'exit_time' in trade:
                duration = (trade['exit_time'] - trade['entry_time']).total_seconds() / 3600  # hours
                trade_durations.append(duration)
        
        avg_trade_duration = np.mean(trade_durations) if trade_durations else 0.0
        
        monthly_equity = equity_series.resample('M').last()
        monthly_returns = monthly_equity.pct_change().dropna()
        
        return BacktestResult(
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=len(trades),
            avg_trade_duration=avg_trade_duration,
            profit_factor=profit_factor,
            calmar_ratio=calmar_ratio,
            sortino_ratio=sortino_ratio,
            var_95=var_95,
            trades=trades,
            equity_curve=equity_series,
            monthly_returns=monthly_returns
        )
    
    def generate_backtest_report(self, result: BacktestResult) -> Dict[str, Any]:
        """Generate comprehensive backtest report"""
        return {
            'performance_summary': {
                'total_return_pct': result.total_return * 100,
                'sharpe_ratio': result.sharpe_ratio,
                'sortino_ratio': result.sortino_ratio,
                'calmar_ratio': result.calmar_ratio,
                'max_drawdown_pct': result.max_drawdown * 100,
                'profit_factor': result.profit_factor,
                'var_95_pct': result.var_95 * 100
            },
            'trade_statistics': {
                'total_trades': result.total_trades,
                'win_rate_pct': result.win_rate * 100,
                'avg_trade_duration_hours': result.avg_trade_duration,
                'best_trade': max(result.trades, key=lambda x: x['pnl'])['pnl'] if result.trades else 0,
                'worst_trade': min(result.trades, key=lambda x: x['pnl'])['pnl'] if result.trades else 0
            },
            'risk_metrics': {
                'volatility_annualized': result.equity_curve.pct_change().std() * np.sqrt(252) if len(result.equity_curve) > 1 else 0,
                'max_consecutive_losses': self._calculate_max_consecutive_losses(result.trades),
                'recovery_factor': abs(result.total_return / result.max_drawdown) if result.max_drawdown > 0 else 0
            }
        }
    
    def _calculate_max_consecutive_losses(self, trades: List[Dict]) -> int:
        """Calculate maximum consecutive losing trades"""
        max_consecutive = 0
        current_consecutive = 0
        
        for trade in trades:
            if trade['pnl'] < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
