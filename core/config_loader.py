"""
Configuration loader for the trading bot
Handles environment variables and configuration management
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class TradingConfig:
    """Trading configuration parameters"""
    default_risk_percent: float = 2.0
    max_drawdown_percent: float = 10.0
    max_daily_trades: int = 10
    trading_enabled: bool = True
    symbol: str = "EURUSD"
    timeframe: str = "M15"
    
    def get(self, key: str, default=None):
        """Dictionary-like get method for compatibility"""
        return getattr(self, key, default)
    
@dataclass
class MT5Config:
    """MT5 broker configuration"""
    login: Optional[str] = None
    password: Optional[str] = None
    server: Optional[str] = None
    path: Optional[str] = None
    
@dataclass
class OpenAIConfig:
    """OpenAI API configuration"""
    api_key: Optional[str] = None
    model: str = "gpt-4"
    max_tokens: int = 1000
    temperature: float = 0.7
    
@dataclass
class TelegramConfig:
    """Telegram bot configuration"""
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    enabled: bool = False

class ConfigLoader:
    """Centralized configuration management"""
    
    def __init__(self, env_file: str = ".env"):
        load_dotenv(env_file)
        self._load_configs()
    
    def _load_configs(self):
        """Load all configuration sections"""
        self.trading = TradingConfig(
            default_risk_percent=float(os.getenv('DEFAULT_RISK_PERCENT', 2.0)),
            max_drawdown_percent=float(os.getenv('MAX_DRAWDOWN_PERCENT', 10.0)),
            max_daily_trades=int(os.getenv('MAX_DAILY_TRADES', 10)),
            trading_enabled=os.getenv('TRADING_ENABLED', 'True').lower() == 'true',
            symbol=os.getenv('TRADING_SYMBOL', 'EURUSD'),
            timeframe=os.getenv('TRADING_TIMEFRAME', 'M15')
        )
        
        self.mt5 = MT5Config(
            login=os.getenv('MT5_LOGIN'),
            password=os.getenv('MT5_PASSWORD'),
            server=os.getenv('MT5_SERVER'),
            path=os.getenv('MT5_PATH')
        )
        
        self.openai = OpenAIConfig(
            api_key=os.getenv('OPENAI_API_KEY'),
            model=os.getenv('OPENAI_MODEL', 'gpt-4'),
            max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', 1000)),
            temperature=float(os.getenv('OPENAI_TEMPERATURE', 0.7))
        )
        
        self.telegram = TelegramConfig(
            bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
            chat_id=os.getenv('TELEGRAM_CHAT_ID'),
            enabled=os.getenv('TELEGRAM_ENABLED', 'False').lower() == 'true'
        )
        
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary"""
        return {
            'trading': self.trading.__dict__,
            'mt5': self.mt5.__dict__,
            'openai': self.openai.__dict__,
            'telegram': self.telegram.__dict__,
            'environment': self.environment,
            'log_level': self.log_level
        }
    
    def save_config(self, filepath: str):
        """Save current configuration to file"""
        with open(filepath, 'w') as f:
            json.dump(self.get_config_dict(), f, indent=2)
    
    def validate_config(self) -> Dict[str, bool]:
        """Validate configuration and return status"""
        validation = {
            'openai_configured': bool(self.openai.api_key),
            'mt5_configured': all([self.mt5.login, self.mt5.password, self.mt5.server]),
            'telegram_configured': bool(self.telegram.bot_token and self.telegram.chat_id),
            'trading_params_valid': (
                0 < self.trading.default_risk_percent <= 10 and
                0 < self.trading.max_drawdown_percent <= 50 and
                self.trading.max_daily_trades > 0
            )
        }
        return validation

config = ConfigLoader()
