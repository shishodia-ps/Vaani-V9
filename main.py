#!/usr/bin/env python3
"""
Forex Trading Bot V9 - Main Entry Point
Agentic AI Forex Trading Bot with Streamlit UI and MT5 Integration
"""

import os
import sys
import logging
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from ui.streamlit_dashboard import main as run_dashboard

def setup_logging():
    """Configure logging for the application"""
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data/logs/trading_bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main entry point for the trading bot"""
    load_dotenv()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Forex Trading Bot V9")
    
    os.makedirs('data/logs', exist_ok=True)
    os.makedirs('data/reports', exist_ok=True)
    os.makedirs('data/raw_price', exist_ok=True)
    os.makedirs('data/volatility_snapshots', exist_ok=True)
    os.makedirs('data/risk_snapshots', exist_ok=True)
    
    try:
        run_dashboard()
    except KeyboardInterrupt:
        logger.info("Trading bot stopped by user")
    except Exception as e:
        logger.error(f"Error running trading bot: {e}")
        raise

if __name__ == "__main__":
    main()
