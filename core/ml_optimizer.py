"""
Machine Learning Optimizer for VaaniV9 Strategy
Provides adaptive learning and optimization from past trades
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
import json
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os

class MLOptimizer:
    """Machine Learning optimizer for strategy parameters and signals"""
    
    def __init__(self, model_path: str = "models/"):
        self.model_path = model_path
        self.logger = logging.getLogger(__name__)
        
        os.makedirs(model_path, exist_ok=True)
        
        self.signal_predictor = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        self.risk_predictor = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        
        self.scaler = StandardScaler()
        
        self.model_performance = {
            'signal_accuracy': 0.0,
            'risk_accuracy': 0.0,
            'last_training': None,
            'training_samples': 0
        }
        
        self._load_models()
    
    def extract_features(self, data: pd.DataFrame, lookback: int = 20) -> np.ndarray:
        """Extract features for ML models"""
        try:
            if len(data) < lookback + 10:
                return np.array([])
            
            features = []
            
            returns = data['close'].pct_change()
            features.extend([
                returns.tail(lookback).mean(),
                returns.tail(lookback).std(),
                returns.tail(lookback).skew(),
                returns.tail(lookback).kurt()
            ])
            
            sma_5 = data['close'].rolling(5).mean()
            sma_20 = data['close'].rolling(20).mean()
            sma_50 = data['close'].rolling(50).mean()
            
            features.extend([
                (data['close'].iloc[-1] - sma_5.iloc[-1]) / sma_5.iloc[-1],
                (data['close'].iloc[-1] - sma_20.iloc[-1]) / sma_20.iloc[-1],
                (data['close'].iloc[-1] - sma_50.iloc[-1]) / sma_50.iloc[-1],
                (sma_5.iloc[-1] - sma_20.iloc[-1]) / sma_20.iloc[-1],
                (sma_20.iloc[-1] - sma_50.iloc[-1]) / sma_50.iloc[-1]
            ])
            
            volatility = returns.rolling(20).std()
            features.extend([
                volatility.iloc[-1],
                volatility.tail(20).mean(),
                volatility.tail(20).std()
            ])
            
            if 'volume' in data.columns:
                volume_sma = data['volume'].rolling(20).mean()
                features.extend([
                    data['volume'].iloc[-1] / volume_sma.iloc[-1],
                    data['volume'].tail(20).std() / volume_sma.iloc[-1]
                ])
            else:
                features.extend([1.0, 0.1])  # Default values
            
            delta = data['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            features.append(rsi.iloc[-1] / 100.0)
            
            ema_12 = data['close'].ewm(span=12).mean()
            ema_26 = data['close'].ewm(span=26).mean()
            macd = ema_12 - ema_26
            signal_line = macd.ewm(span=9).mean()
            features.extend([
                macd.iloc[-1] / data['close'].iloc[-1],
                (macd.iloc[-1] - signal_line.iloc[-1]) / data['close'].iloc[-1]
            ])
            
            trend_strength = abs(returns.tail(20).mean()) / returns.tail(20).std()
            features.append(trend_strength)
            
            hour = data.index[-1].hour if hasattr(data.index[-1], 'hour') else 12
            day_of_week = data.index[-1].dayofweek if hasattr(data.index[-1], 'dayofweek') else 1
            features.extend([
                np.sin(2 * np.pi * hour / 24),
                np.cos(2 * np.pi * hour / 24),
                np.sin(2 * np.pi * day_of_week / 7),
                np.cos(2 * np.pi * day_of_week / 7)
            ])
            
            return np.array(features)
            
        except Exception as e:
            self.logger.error(f"Feature extraction error: {e}")
            return np.array([])
    
    def train_models(self, historical_data: pd.DataFrame, trade_history: List[Dict]) -> Dict[str, float]:
        """Train ML models on historical data and trade outcomes"""
        try:
            if len(historical_data) < 200 or len(trade_history) < 50:
                self.logger.warning("Insufficient data for ML training")
                return self.model_performance
            
            X, y_signal, y_risk = self._prepare_training_data(historical_data, trade_history)
            
            if len(X) < 50:
                return self.model_performance
            
            X_scaled = self.scaler.fit_transform(X)
            
            tscv = TimeSeriesSplit(n_splits=3)
            
            signal_scores = []
            for train_idx, val_idx in tscv.split(X_scaled):
                X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
                y_train, y_val = y_signal[train_idx], y_signal[val_idx]
                
                self.signal_predictor.fit(X_train, y_train)
                y_pred = self.signal_predictor.predict(X_val)
                score = r2_score(y_val, y_pred)
                signal_scores.append(score)
            
            risk_scores = []
            for train_idx, val_idx in tscv.split(X_scaled):
                X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
                y_train, y_val = y_risk[train_idx], y_risk[val_idx]
                
                self.risk_predictor.fit(X_train, y_train)
                y_pred = self.risk_predictor.predict(X_val)
                score = r2_score(y_val, y_pred)
                risk_scores.append(score)
            
            self.signal_predictor.fit(X_scaled, y_signal)
            self.risk_predictor.fit(X_scaled, y_risk)
            
            self.model_performance.update({
                'signal_accuracy': np.mean(signal_scores),
                'risk_accuracy': np.mean(risk_scores),
                'last_training': datetime.now(),
                'training_samples': len(X)
            })
            
            self._save_models()
            
            self.logger.info(f"ML models trained successfully. Signal R²: {np.mean(signal_scores):.3f}, Risk R²: {np.mean(risk_scores):.3f}")
            
            return self.model_performance
            
        except Exception as e:
            self.logger.error(f"ML training error: {e}")
            return self.model_performance
    
    def _prepare_training_data(self, data: pd.DataFrame, trades: List[Dict]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Prepare training data from historical data and trades"""
        
        features = []
        signal_targets = []
        risk_targets = []
        
        for i in range(100, len(data) - 10):  # Leave some data for forward-looking targets
            
            current_data = data.iloc[:i+1]
            feature_vector = self.extract_features(current_data)
            
            if len(feature_vector) == 0:
                continue
            
            future_returns = []
            for j in range(1, 11):  # Look ahead 10 periods
                if i + j < len(data):
                    ret = (data['close'].iloc[i + j] - data['close'].iloc[i]) / data['close'].iloc[i]
                    future_returns.append(ret)
            
            if not future_returns:
                continue
            
            signal_target = np.mean(future_returns)
            
            risk_target = np.std(future_returns) if len(future_returns) > 1 else 0.0
            
            features.append(feature_vector)
            signal_targets.append(signal_target)
            risk_targets.append(risk_target)
        
        for trade in trades:
            if 'features' in trade and 'pnl' in trade:
                features.append(trade['features'])
                signal_targets.append(trade['pnl'] / 1000.0)  # Normalize by typical trade size
                risk_targets.append(abs(trade['pnl']) / 1000.0)
        
        return np.array(features), np.array(signal_targets), np.array(risk_targets)
    
    def predict_signal_strength(self, data: pd.DataFrame) -> float:
        """Predict signal strength using trained model"""
        try:
            features = self.extract_features(data)
            if len(features) == 0:
                return 0.0
            
            features_scaled = self.scaler.transform(features.reshape(1, -1))
            prediction = self.signal_predictor.predict(features_scaled)[0]
            
            return np.tanh(prediction * 5)
            
        except Exception as e:
            self.logger.error(f"Signal prediction error: {e}")
            return 0.0
    
    def predict_risk_level(self, data: pd.DataFrame) -> float:
        """Predict risk level using trained model"""
        try:
            features = self.extract_features(data)
            if len(features) == 0:
                return 0.5
            
            features_scaled = self.scaler.transform(features.reshape(1, -1))
            prediction = self.risk_predictor.predict(features_scaled)[0]
            
            return max(0.0, min(1.0, prediction))
            
        except Exception as e:
            self.logger.error(f"Risk prediction error: {e}")
            return 0.5
    
    def optimize_parameters(self, strategy, data: pd.DataFrame, 
                          parameter_ranges: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
        """Optimize strategy parameters using ML-guided search"""
        try:
            best_params = {}
            best_score = -float('inf')
            
            param_combinations = self._generate_parameter_combinations(parameter_ranges, n_samples=50)
            
            for params in param_combinations:
                for param, value in params.items():
                    if hasattr(strategy, param):
                        setattr(strategy, param, value)
                
                score = self._evaluate_strategy_performance(strategy, data)
                
                if score > best_score:
                    best_score = score
                    best_params = params.copy()
            
            self.logger.info(f"Parameter optimization completed. Best score: {best_score:.3f}")
            return best_params
            
        except Exception as e:
            self.logger.error(f"Parameter optimization error: {e}")
            return {}
    
    def _generate_parameter_combinations(self, ranges: Dict[str, Tuple[float, float]], 
                                       n_samples: int = 50) -> List[Dict[str, float]]:
        """Generate parameter combinations for optimization"""
        combinations = []
        
        for _ in range(n_samples):
            combination = {}
            for param, (min_val, max_val) in ranges.items():
                combination[param] = np.random.uniform(min_val, max_val)
            combinations.append(combination)
        
        return combinations
    
    def _evaluate_strategy_performance(self, strategy, data: pd.DataFrame) -> float:
        """Evaluate strategy performance for parameter optimization"""
        try:
            signals = []
            returns = []
            
            for i in range(100, len(data)):
                current_data = data.iloc[:i+1]
                result = strategy.analyze(current_data)
                signal = result.get('signal', 'HOLD')
                confidence = result.get('confidence', 0.0)
                
                if signal == 'BUY' and confidence > 0.6:
                    signals.append(1)
                elif signal == 'SELL' and confidence > 0.6:
                    signals.append(-1)
                else:
                    signals.append(0)
                
                if i + 1 < len(data):
                    ret = (data['close'].iloc[i + 1] - data['close'].iloc[i]) / data['close'].iloc[i]
                    returns.append(ret)
                else:
                    returns.append(0)
            
            strategy_returns = np.array(signals[:-1]) * np.array(returns)
            
            if len(strategy_returns) > 0 and np.std(strategy_returns) > 0:
                return np.mean(strategy_returns) / np.std(strategy_returns) * np.sqrt(252)
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Performance evaluation error: {e}")
            return 0.0
    
    def _save_models(self):
        """Save trained models to disk"""
        try:
            joblib.dump(self.signal_predictor, os.path.join(self.model_path, 'signal_predictor.pkl'))
            joblib.dump(self.risk_predictor, os.path.join(self.model_path, 'risk_predictor.pkl'))
            joblib.dump(self.scaler, os.path.join(self.model_path, 'scaler.pkl'))
            
            with open(os.path.join(self.model_path, 'performance.json'), 'w') as f:
                perf_data = self.model_performance.copy()
                if perf_data['last_training']:
                    perf_data['last_training'] = perf_data['last_training'].isoformat()
                json.dump(perf_data, f)
                
        except Exception as e:
            self.logger.error(f"Model saving error: {e}")
    
    def _load_models(self):
        """Load existing models from disk"""
        try:
            signal_path = os.path.join(self.model_path, 'signal_predictor.pkl')
            risk_path = os.path.join(self.model_path, 'risk_predictor.pkl')
            scaler_path = os.path.join(self.model_path, 'scaler.pkl')
            perf_path = os.path.join(self.model_path, 'performance.json')
            
            if all(os.path.exists(p) for p in [signal_path, risk_path, scaler_path]):
                self.signal_predictor = joblib.load(signal_path)
                self.risk_predictor = joblib.load(risk_path)
                self.scaler = joblib.load(scaler_path)
                
                if os.path.exists(perf_path):
                    with open(perf_path, 'r') as f:
                        perf_data = json.load(f)
                        if perf_data.get('last_training'):
                            perf_data['last_training'] = datetime.fromisoformat(perf_data['last_training'])
                        self.model_performance.update(perf_data)
                
                self.logger.info("ML models loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Model loading error: {e}")
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status and performance"""
        return {
            'models_trained': self.model_performance['training_samples'] > 0,
            'signal_accuracy': self.model_performance['signal_accuracy'],
            'risk_accuracy': self.model_performance['risk_accuracy'],
            'last_training': self.model_performance['last_training'].isoformat() if self.model_performance['last_training'] else None,
            'training_samples': self.model_performance['training_samples']
        }
