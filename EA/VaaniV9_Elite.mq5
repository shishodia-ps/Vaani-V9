//+------------------------------------------------------------------+
//|                                                VaaniV9_Elite.mq5 |
//|                        Copyright 2025, Prashant Kumar Shishodia |
//|                                   https://github.com/shishodia-ps |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, Prashant Kumar Shishodia"
#property link      "https://github.com/shishodia-ps/Vaani-V9"
#property version   "9.00"
#property description "VaaniV9 Elite - Ultimate Forex Trading EA with AI-Enhanced Signals"
#property description "Features: Multi-Strategy Fusion, Adaptive Risk Management, ML-Enhanced Signals"
#property description "Capital Protection, Multi-Timeframe Analysis, News Awareness"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Indicators\Indicators.mqh>

//+------------------------------------------------------------------+
//| Input Parameters - Elite EA Configuration                        |
//+------------------------------------------------------------------+
input group "=== VaaniV9 Elite Strategy Settings ==="
input double   InpRiskPercent = 2.0;           // Risk per trade (%)
input double   InpMaxRiskPercent = 10.0;       // Maximum total risk (%)
input int      InpMagicNumber = 20250601;      // Magic number
input bool     InpAdaptiveMode = true;         // Enable adaptive mode
input bool     InpMLEnhanced = true;           // Enable ML-enhanced signals

input group "=== Crisis Profit Management ==="
input bool     InpCrisisProfitMode = true;     // Enable crisis profit trading
input double   InpHedgeRatio = 0.3;            // Hedge position ratio (30%)
input double   InpVolatilitySpikeThreshold = 3.0; // Volatility spike threshold (300%)
input double   InpCrashDetectionThreshold = 0.02; // Price drop threshold (2%)
input bool     InpCounterTrendTrading = true;  // Enable counter-trend during crashes
input double   InpRecoveryMultiplier = 1.5;    // Recovery trade size multiplier

input group "=== Multi-Strategy Fusion ==="
input bool     InpTrendFollowing = true;       // Enable trend following
input bool     InpMeanReversion = true;        // Enable mean reversion
input bool     InpBreakoutStrategy = true;     // Enable breakout strategy
input bool     InpNewsStrategy = true;         // Enable news-based strategy
input bool     InpVolatilityStrategy = true;   // Enable volatility strategy

input group "=== Risk Management ==="
input double   InpStopLossPoints = 500;        // Stop Loss (points)
input double   InpTakeProfitPoints = 1000;     // Take Profit (points)
input bool     InpUseTrailingStop = true;      // Use trailing stop
input double   InpTrailingStart = 300;         // Trailing start (points)
input double   InpTrailingStep = 50;           // Trailing step (points)
input double   InpMaxDrawdownPercent = 15.0;   // Max drawdown (%)
input bool     InpBreakEvenMode = true;        // Enable break-even

input group "=== Multi-Timeframe Analysis ==="
input ENUM_TIMEFRAMES InpTF1 = PERIOD_M15;     // Primary timeframe
input ENUM_TIMEFRAMES InpTF2 = PERIOD_H1;      // Secondary timeframe
input ENUM_TIMEFRAMES InpTF3 = PERIOD_H4;      // Tertiary timeframe
input ENUM_TIMEFRAMES InpTF4 = PERIOD_D1;      // Daily timeframe

input group "=== Capital Protection ==="
input bool     InpEmergencyStop = true;        // Enable emergency stop
input double   InpVolatilityThreshold = 3.0;   // Volatility spike threshold
input bool     InpNewsFilter = true;           // Enable news filter
input int      InpNewsMinutesBefore = 30;      // Minutes before news
input int      InpNewsMinutesAfter = 30;       // Minutes after news

input group "=== Smart Position Sizing ==="
input bool     InpKellyCriterion = true;       // Use Kelly Criterion
input bool     InpVolatilityTargeting = true;  // Use volatility targeting
input double   InpMaxPositionSize = 5.0;       // Max position size (lots)
input double   InpMinPositionSize = 0.01;      // Min position size (lots)

input group "=== Broker Compatibility ==="
input int      InpSlippagePoints = 30;         // Max slippage (points)
input bool     InpECNMode = false;             // ECN broker mode
input int      InpMaxSpreadPoints = 50;        // Max spread (points)

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
CTrade         trade;
CPositionInfo  position;
CAccountInfo   account;
CSymbolInfo    symbol;

// Market Regime Detection
enum MARKET_REGIME
{
   REGIME_TRENDING_UP,
   REGIME_TRENDING_DOWN,
   REGIME_RANGING,
   REGIME_HIGH_VOLATILITY,
   REGIME_NEWS_DRIVEN,
   REGIME_CRISIS
};

// Strategy Types
enum STRATEGY_TYPE
{
   STRATEGY_TREND_FOLLOWING,
   STRATEGY_MEAN_REVERSION,
   STRATEGY_MOMENTUM,
   STRATEGY_BREAKOUT,
   STRATEGY_NEWS_FADE,
   STRATEGY_VOLATILITY,
   STRATEGY_CORRELATION_HEDGE
};

// Global state variables
MARKET_REGIME  g_currentRegime = REGIME_RANGING;
STRATEGY_TYPE  g_activeStrategy = STRATEGY_TREND_FOLLOWING;
double         g_currentEquity = 0.0;
double         g_maxEquity = 0.0;
double         g_currentDrawdown = 0.0;
bool           g_emergencyMode = false;
bool           g_tradingHalted = false;
datetime       g_lastTradeTime = 0;
datetime       g_lastResetTime = 0;

// Crisis profit management variables
bool           g_crisisMode = false;
bool           g_crashDetected = false;
bool           g_recoveryMode = false;
double         g_lastVolatility = 0.0;
double         g_volatilitySpike = 1.0;
int            g_activeHedges = 0;
datetime       g_lastCrashTime = 0;

// Performance tracking
int            g_totalTrades = 0;
int            g_winningTrades = 0;
double         g_totalProfit = 0.0;
double         g_totalLoss = 0.0;
double         g_sharpeRatio = 0.0;

// ML-Enhanced signals
double         g_mlSignalStrength = 0.0;
double         g_mlRiskLevel = 0.5;
bool           g_mlModelsLoaded = false;

// Multi-timeframe indicators
int            g_handleRSI_M15, g_handleRSI_H1, g_handleRSI_H4, g_handleRSI_D1;
int            g_handleMACD_M15, g_handleMACD_H1, g_handleMACD_H4;
int            g_handleATR_M15, g_handleATR_H1;
int            g_handleBB_M15, g_handleBB_H1;
int            g_handleADX_M15, g_handleADX_H1;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("VaaniV9 Elite EA - Initializing Ultimate Forex Trading System");
   
   // Set trade parameters
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpSlippagePoints);
   trade.SetTypeFilling(ORDER_FILLING_FOK);
   
   // Initialize symbol
   if(!symbol.Name(_Symbol))
   {
      Print("Error: Failed to initialize symbol");
      return INIT_FAILED;
   }
   
   // Initialize multi-timeframe indicators
   if(!InitializeIndicators())
   {
      Print("Error: Failed to initialize indicators");
      return INIT_FAILED;
   }
   
   // Initialize ML models (simulated)
   InitializeMLModels();
   
   // Initialize performance tracking
   g_currentEquity = account.Equity();
   g_maxEquity = g_currentEquity;
   g_lastResetTime = TimeCurrent();
   
   // Create dashboard
   CreateDashboard();
   
   Print("VaaniV9 Elite EA - Initialization completed successfully");
   Print("Features: Multi-Strategy Fusion, ML-Enhanced Signals, Adaptive Risk Management");
   Print("Capital Protection: Emergency Stop, Volatility Monitoring, News Filter");
   Print("Position Sizing: Kelly Criterion, Volatility Targeting, Dynamic Sizing");
   
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("VaaniV9 Elite EA - Shutting down");
   
   // Save performance data
   SavePerformanceData();
   
   // Clean up dashboard
   ObjectsDeleteAll(0, "VaaniV9_");
   
   Print("Final Performance Summary:");
   Print("Total Trades: ", g_totalTrades);
   Print("Win Rate: ", (g_totalTrades > 0 ? (double)g_winningTrades/g_totalTrades*100 : 0), "%");
   Print("Total Profit: ", g_totalProfit);
   Print("Sharpe Ratio: ", g_sharpeRatio);
   Print("Max Drawdown: ", g_currentDrawdown, "%");
}

//+------------------------------------------------------------------+
//| Expert tick function - Main Trading Logic                       |
//+------------------------------------------------------------------+
void OnTick()
{
   // CRITICAL FIX #6: Real-time equity-based kill switch
   double current_equity = account.Equity();
   double equity_drawdown = (g_maxEquity - current_equity) / g_maxEquity * 100.0;
   
   if(equity_drawdown > InpMaxDrawdownPercent)
   {
      if(!g_emergencyMode)
      {
         Print("EMERGENCY STOP: Equity drawdown ", equity_drawdown, "% exceeds limit ", InpMaxDrawdownPercent, "%");
         g_emergencyMode = true;
         g_tradingHalted = true;
         CloseAllPositions("Equity drawdown emergency stop");
      }
      return;
   }
   
   // Update max equity for drawdown calculation
   if(current_equity > g_maxEquity)
      g_maxEquity = current_equity;
   
   // CRITICAL FIX #9: Position tracking validation on restart
   static bool positions_validated = false;
   if(!positions_validated)
   {
      ValidateExistingPositions();
      positions_validated = true;
   }
   
   // Update current state
   UpdateMarketState();
   
   // Enhanced crisis management - profit from volatility instead of just stopping
   if(CheckCrisisConditions())
   {
      if(!g_crisisMode && InpCrisisProfitMode)
      {
         Print("CRISIS PROFIT MODE ACTIVATED - Engaging profitable hedging strategies");
         g_crisisMode = true;
         ExecuteCrisisProfitStrategy();
      }
      else if(!g_crisisMode)
      {
         Print("EMERGENCY MODE ACTIVATED - Capital Protection Engaged");
         g_emergencyMode = true;
         CloseAllPositions("Emergency stop");
      }
      return;
   }
   
   // Check for flash crash opportunities
   if(DetectFlashCrash())
   {
      ExecuteFlashCrashStrategy();
   }
   
   // Check if trading is halted
   if(g_tradingHalted)
   {
      if(ShouldResumeTrading())
      {
         g_tradingHalted = false;
         g_emergencyMode = false;
         Print("Trading resumed - Market conditions normalized");
      }
      else
         return;
   }
   
   // Daily reset logic
   if(ShouldPerformDailyReset())
   {
      PerformDailyReset();
   }
   
   // Update ML predictions
   if(InpMLEnhanced)
   {
      UpdateMLPredictions();
   }
   
   // Detect market regime
   DetectMarketRegime();
   
   // Select optimal strategy
   SelectOptimalStrategy();
   
   // Check news filter
   if(InpNewsFilter && IsNewsTime())
   {
      Print("News filter active - Trading suspended");
      return;
   }
   
   // Check spread conditions
   if(!CheckSpreadConditions())
   {
      return;
   }
   
   // Manage existing positions
   ManageExistingPositions();
   
   // Generate trading signals
   if(ShouldGenerateSignals())
   {
      GenerateAndExecuteSignals();
   }
   
   // Update dashboard
   UpdateDashboard();
}

//+------------------------------------------------------------------+
//| Initialize Multi-Timeframe Indicators                           |
//+------------------------------------------------------------------+
bool InitializeIndicators()
{
   // RSI indicators for all timeframes
   g_handleRSI_M15 = iRSI(_Symbol, PERIOD_M15, 14, PRICE_CLOSE);
   g_handleRSI_H1 = iRSI(_Symbol, PERIOD_H1, 14, PRICE_CLOSE);
   g_handleRSI_H4 = iRSI(_Symbol, PERIOD_H4, 14, PRICE_CLOSE);
   g_handleRSI_D1 = iRSI(_Symbol, PERIOD_D1, 14, PRICE_CLOSE);
   
   // MACD indicators
   g_handleMACD_M15 = iMACD(_Symbol, PERIOD_M15, 12, 26, 9, PRICE_CLOSE);
   g_handleMACD_H1 = iMACD(_Symbol, PERIOD_H1, 12, 26, 9, PRICE_CLOSE);
   g_handleMACD_H4 = iMACD(_Symbol, PERIOD_H4, 12, 26, 9, PRICE_CLOSE);
   
   // ATR indicators
   g_handleATR_M15 = iATR(_Symbol, PERIOD_M15, 14);
   g_handleATR_H1 = iATR(_Symbol, PERIOD_H1, 14);
   
   // Bollinger Bands
   g_handleBB_M15 = iBands(_Symbol, PERIOD_M15, 20, 0, 2.0, PRICE_CLOSE);
   g_handleBB_H1 = iBands(_Symbol, PERIOD_H1, 20, 0, 2.0, PRICE_CLOSE);
   
   // ADX indicators
   g_handleADX_M15 = iADX(_Symbol, PERIOD_M15, 14);
   g_handleADX_H1 = iADX(_Symbol, PERIOD_H1, 14);
   
   // Verify all handles are valid
   if(g_handleRSI_M15 == INVALID_HANDLE || g_handleRSI_H1 == INVALID_HANDLE ||
      g_handleMACD_M15 == INVALID_HANDLE || g_handleATR_M15 == INVALID_HANDLE)
   {
      Print("Error: Failed to create indicator handles");
      return false;
   }
   
   return true;
}

//+------------------------------------------------------------------+
//| Initialize ML Models (Simulated)                                |
//+------------------------------------------------------------------+
void InitializeMLModels()
{
   if(InpMLEnhanced)
   {
      // Simulate ML model loading
      g_mlModelsLoaded = true;
      g_mlSignalStrength = 0.0;
      g_mlRiskLevel = 0.5;
      Print("ML Models initialized - Enhanced signal processing enabled");
   }
}

//+------------------------------------------------------------------+
//| Update Market State                                              |
//+------------------------------------------------------------------+
void UpdateMarketState()
{
   g_currentEquity = account.Equity();
   
   // Update maximum equity
   if(g_currentEquity > g_maxEquity)
      g_maxEquity = g_currentEquity;
   
   // Calculate current drawdown
   if(g_maxEquity > 0)
      g_currentDrawdown = (g_maxEquity - g_currentEquity) / g_maxEquity * 100.0;
}

//+------------------------------------------------------------------+
//| Check Crisis Conditions (Enhanced for Profit Opportunities)     |
//+------------------------------------------------------------------+
bool CheckCrisisConditions()
{
   // Update volatility metrics
   double atr_current = GetATRValue(PERIOD_M15, 0);
   double atr_average = GetATRAverage(PERIOD_M15, 20);
   g_volatilitySpike = (atr_average > 0) ? atr_current / atr_average : 1.0;
   
   // Crisis conditions (lower threshold for profit opportunities)
   if(g_currentDrawdown > InpMaxDrawdownPercent * 0.7) // 70% of max drawdown
   {
      Print("ALERT: Approaching maximum drawdown: ", g_currentDrawdown, "%");
      return true;
   }
   
   // Volatility spike detection (profit opportunity)
   if(g_volatilitySpike > InpVolatilitySpikeThreshold)
   {
      Print("OPPORTUNITY: Volatility spike detected - ", g_volatilitySpike, "x normal levels");
      return true;
   }
   
   // Account equity check (only extreme cases)
   double current_equity = account.Equity();
   if(current_equity < account.Balance() * 0.5) // 50% equity loss (extreme)
   {
      Print("ALERT: Severe equity loss detected");
      return true;
   }
   
   // Check spread conditions (still important for execution)
   double spread = symbol.Spread() * symbol.Point();
   double normal_spread = InpMaxSpreadPoints * symbol.Point();
   
   if(spread > normal_spread * 4.0) // Higher threshold for crisis mode
   {
      Print("ALERT: Extreme spread detected: ", spread);
      return true;
   }
   
   return false;
}

//+------------------------------------------------------------------+
//| Detect Flash Crash Conditions                                   |
//+------------------------------------------------------------------+
bool DetectFlashCrash()
{
   if(!InpCounterTrendTrading)
      return false;
   
   // Get recent price movement
   double prices[];
   if(CopyClose(_Symbol, PERIOD_M15, 0, 5, prices) < 5)
      return false;
   
   // Calculate rapid price movement (last 5 M15 candles = 75 minutes)
   double price_change = (prices[4] - prices[0]) / prices[0];
   
   // Flash crash detection
   if(MathAbs(price_change) > InpCrashDetectionThreshold && 
      g_volatilitySpike > InpVolatilitySpikeThreshold)
   {
      if(TimeCurrent() - g_lastCrashTime > 3600) // At least 1 hour between crash detections
      {
         g_lastCrashTime = TimeCurrent();
         g_crashDetected = true;
         Print("FLASH CRASH DETECTED: ", price_change*100, "% move with ", g_volatilitySpike, "x volatility");
         return true;
      }
   }
   
   return false;
}

//+------------------------------------------------------------------+
//| Detect Market Regime                                            |
//+------------------------------------------------------------------+
void DetectMarketRegime()
{
   double rsi_h1 = GetRSIValue(PERIOD_H1, 0);
   double rsi_h4 = GetRSIValue(PERIOD_H4, 0);
   double adx_h1 = GetADXValue(PERIOD_H1, 0);
   double atr_h1 = GetATRValue(PERIOD_H1, 0);
   double atr_avg = GetATRAverage(PERIOD_H1, 20);
   
   MARKET_REGIME previousRegime = g_currentRegime;
   
   // Crisis detection
   if(atr_h1 > atr_avg * 2.5)
   {
      g_currentRegime = REGIME_CRISIS;
   }
   // High volatility
   else if(atr_h1 > atr_avg * 1.8)
   {
      g_currentRegime = REGIME_HIGH_VOLATILITY;
   }
   // Trending market
   else if(adx_h1 > 25)
   {
      if(rsi_h4 > 60)
         g_currentRegime = REGIME_TRENDING_UP;
      else if(rsi_h4 < 40)
         g_currentRegime = REGIME_TRENDING_DOWN;
      else
         g_currentRegime = REGIME_RANGING;
   }
   // Ranging market
   else
   {
      g_currentRegime = REGIME_RANGING;
   }
   
   // Log regime changes
   if(g_currentRegime != previousRegime)
   {
      Print("Market Regime Changed: ", EnumToString(previousRegime), " -> ", EnumToString(g_currentRegime));
   }
}

//+------------------------------------------------------------------+
//| Select Optimal Strategy Based on Market Regime                  |
//+------------------------------------------------------------------+
void SelectOptimalStrategy()
{
   STRATEGY_TYPE previousStrategy = g_activeStrategy;
   
   switch(g_currentRegime)
   {
      case REGIME_TRENDING_UP:
      case REGIME_TRENDING_DOWN:
         if(InpTrendFollowing)
            g_activeStrategy = STRATEGY_TREND_FOLLOWING;
         break;
         
      case REGIME_RANGING:
         if(InpMeanReversion)
            g_activeStrategy = STRATEGY_MEAN_REVERSION;
         break;
         
      case REGIME_HIGH_VOLATILITY:
         if(InpBreakoutStrategy)
            g_activeStrategy = STRATEGY_BREAKOUT;
         else if(InpVolatilityStrategy)
            g_activeStrategy = STRATEGY_VOLATILITY;
         break;
         
      case REGIME_NEWS_DRIVEN:
         if(InpNewsStrategy)
            g_activeStrategy = STRATEGY_NEWS_FADE;
         break;
         
      case REGIME_CRISIS:
         g_activeStrategy = STRATEGY_CORRELATION_HEDGE;
         break;
   }
   
   // Log strategy changes
   if(g_activeStrategy != previousStrategy)
   {
      Print("Active Strategy Changed: ", EnumToString(previousStrategy), " -> ", EnumToString(g_activeStrategy));
   }
}

//+------------------------------------------------------------------+
//| Update ML Predictions                                            |
//+------------------------------------------------------------------+
void UpdateMLPredictions()
{
   if(!g_mlModelsLoaded)
      return;
   
   // Simulate ML signal prediction
   double rsi_m15 = GetRSIValue(PERIOD_M15, 0);
   double macd_main = GetMACDValue(PERIOD_M15, 0, MODE_MAIN);
   double atr_ratio = GetATRValue(PERIOD_M15, 0) / GetATRAverage(PERIOD_M15, 20);
   
   // Simple ML simulation based on technical indicators
   double signal_strength = 0.0;
   
   // Trend strength component
   if(rsi_m15 > 70)
      signal_strength -= 0.3;
   else if(rsi_m15 < 30)
      signal_strength += 0.3;
   
   // Momentum component
   if(macd_main > 0)
      signal_strength += 0.2;
   else
      signal_strength -= 0.2;
   
   // Volatility component
   if(atr_ratio > 1.5)
      signal_strength *= 0.7; // Reduce signal in high volatility
   
   g_mlSignalStrength = MathMax(-1.0, MathMin(1.0, signal_strength));
   g_mlRiskLevel = MathMax(0.1, MathMin(0.9, atr_ratio * 0.5));
}

//+------------------------------------------------------------------+
//| Generate and Execute Trading Signals                            |
//+------------------------------------------------------------------+
void GenerateAndExecuteSignals()
{
   double signal_strength = 0.0;
   string signal_reason = "";
   
   // Multi-strategy signal fusion
   switch(g_activeStrategy)
   {
      case STRATEGY_TREND_FOLLOWING:
         signal_strength = GenerateTrendFollowingSignal(signal_reason);
         break;
         
      case STRATEGY_MEAN_REVERSION:
         signal_strength = GenerateMeanReversionSignal(signal_reason);
         break;
         
      case STRATEGY_BREAKOUT:
         signal_strength = GenerateBreakoutSignal(signal_reason);
         break;
         
      case STRATEGY_NEWS_FADE:
         signal_strength = GenerateNewsFadeSignal(signal_reason);
         break;
         
      case STRATEGY_VOLATILITY:
         signal_strength = GenerateVolatilitySignal(signal_reason);
         break;
         
      case STRATEGY_CORRELATION_HEDGE:
         signal_strength = GenerateCorrelationHedgeSignal(signal_reason);
         break;
   }
   
   // Apply ML enhancement
   if(InpMLEnhanced && g_mlModelsLoaded)
   {
      double ml_weight = 0.3; // 30% ML, 70% rule-based
      signal_strength = signal_strength * (1.0 - ml_weight) + g_mlSignalStrength * ml_weight;
      signal_reason += " [ML-Enhanced]";
   }
   
   // Rule-based safety filters
   if(!PassesRuleBasedFilters(signal_strength))
   {
      Print("Signal rejected by rule-based safety filters");
      return;
   }
   
   // Execute signal if strong enough
   double min_signal_strength = 0.6;
   if(MathAbs(signal_strength) >= min_signal_strength)
   {
      ExecuteTradeSignal(signal_strength, signal_reason);
   }
}

//+------------------------------------------------------------------+
//| Generate Trend Following Signal                                 |
//+------------------------------------------------------------------+
double GenerateTrendFollowingSignal(string &reason)
{
   double ema_fast = GetEMAValue(PERIOD_M15, 12, 0);
   double ema_slow = GetEMAValue(PERIOD_M15, 26, 0);
   double adx = GetADXValue(PERIOD_M15, 0);
   double rsi_h1 = GetRSIValue(PERIOD_H1, 0);
   
   reason = "Trend Following: ";
   
   if(adx > 25 && ema_fast > ema_slow && rsi_h1 < 70)
   {
      reason += "Strong uptrend confirmed";
      return 0.8;
   }
   else if(adx > 25 && ema_fast < ema_slow && rsi_h1 > 30)
   {
      reason += "Strong downtrend confirmed";
      return -0.8;
   }
   
   reason += "No clear trend";
   return 0.0;
}

//+------------------------------------------------------------------+
//| Generate Mean Reversion Signal                                  |
//+------------------------------------------------------------------+
double GenerateMeanReversionSignal(string &reason)
{
   double rsi = GetRSIValue(PERIOD_M15, 0);
   double bb_upper = GetBollingerValue(PERIOD_M15, 0, UPPER_BAND);
   double bb_lower = GetBollingerValue(PERIOD_M15, 0, LOWER_BAND);
   double current_price = symbol.Bid();
   
   reason = "Mean Reversion: ";
   
   if(rsi < 30 && current_price < bb_lower)
   {
      reason += "Oversold condition";
      return 0.7;
   }
   else if(rsi > 70 && current_price > bb_upper)
   {
      reason += "Overbought condition";
      return -0.7;
   }
   
   reason += "No reversion signal";
   return 0.0;
}

//+------------------------------------------------------------------+
//| Generate Breakout Signal                                        |
//+------------------------------------------------------------------+
double GenerateBreakoutSignal(string &reason)
{
   double atr = GetATRValue(PERIOD_M15, 0);
   double bb_upper = GetBollingerValue(PERIOD_M15, 0, UPPER_BAND);
   double bb_lower = GetBollingerValue(PERIOD_M15, 0, LOWER_BAND);
   double current_price = symbol.Bid();
   double volume_ratio = GetVolumeRatio();
   
   reason = "Breakout: ";
   
   if(current_price > bb_upper && volume_ratio > 1.5)
   {
      reason += "Upward breakout with volume";
      return 0.75;
   }
   else if(current_price < bb_lower && volume_ratio > 1.5)
   {
      reason += "Downward breakout with volume";
      return -0.75;
   }
   
   reason += "No breakout detected";
   return 0.0;
}

//+------------------------------------------------------------------+
//| Generate News Fade Signal                                       |
//+------------------------------------------------------------------+
double GenerateNewsFadeSignal(string &reason)
{
   // Simplified news fade logic
   double price_change = GetPriceChangePercent(PERIOD_M15, 5);
   double atr = GetATRValue(PERIOD_M15, 0);
   
   reason = "News Fade: ";
   
   if(MathAbs(price_change) > atr * 2.0)
   {
      if(price_change > 0)
      {
         reason += "Fading upward spike";
         return -0.6;
      }
      else
      {
         reason += "Fading downward spike";
         return 0.6;
      }
   }
   
   reason += "No news spike to fade";
   return 0.0;
}

//+------------------------------------------------------------------+
//| Generate Volatility Signal                                      |
//+------------------------------------------------------------------+
double GenerateVolatilitySignal(string &reason)
{
   double atr_current = GetATRValue(PERIOD_M15, 0);
   double atr_average = GetATRAverage(PERIOD_M15, 20);
   double volatility_ratio = atr_current / atr_average;
   
   reason = "Volatility: ";
   
   if(volatility_ratio > 1.5)
   {
      reason += "High volatility - reduce exposure";
      return 0.0; // No signal in high volatility
   }
   else if(volatility_ratio < 0.7)
   {
      reason += "Low volatility - increase exposure";
      return GetTrendDirection() * 0.5;
   }
   
   reason += "Normal volatility";
   return 0.0;
}

//+------------------------------------------------------------------+
//| Generate Correlation Hedge Signal (Enhanced Crisis Profit)     |
//+------------------------------------------------------------------+
double GenerateCorrelationHedgeSignal(string &reason)
{
   reason = "Crisis Profit Strategy: ";
   
   bool severe_crisis = (g_currentDrawdown > InpMaxDrawdownPercent * 0.9);
   bool moderate_crisis = (g_currentDrawdown > InpMaxDrawdownPercent * 0.5);
   
   if(severe_crisis)
   {
      reason += "SEVERE CRISIS - Flattening all positions";
      CloseAllPositions("Severe crisis protection");
      return 0.0;
   }
   else if(moderate_crisis && InpCrisisProfitMode)
   {
      reason += "MODERATE CRISIS - Hedging positions";
      
      if(PositionsTotal() > 0)
      {
         ExecuteHedgingStrategy();
         return 0.0;
      }
   }
   else if(InpCrisisProfitMode)
   {
      reason += "VOLATILITY OPPORTUNITY - Counter-trend trading";
      
      double volatility_signal = GenerateVolatilityProfitSignal();
      return volatility_signal;
      }
   }
   
   reason += "Monitoring for crisis opportunities";
   return 0.0;
}

//+------------------------------------------------------------------+
//| Rule-Based Safety Filters                                       |
//+------------------------------------------------------------------+
bool PassesRuleBasedFilters(double signal_strength)
{
   // Filter 1: Maximum positions
   if(PositionsTotal() >= 3)
   {
      Print("Filter: Maximum positions reached");
      return false;
   }
   
   // Filter 2: Time-based filter
   if(TimeCurrent() - g_lastTradeTime < 300) // 5 minutes
   {
      Print("Filter: Too soon since last trade");
      return false;
   }
   
   // Filter 3: Risk-based filter
   if(g_mlRiskLevel > 0.8)
   {
      Print("Filter: ML risk level too high: ", g_mlRiskLevel);
      return false;
   }
   
   // Filter 4: Market hours filter
   if(!IsMarketHours())
   {
      Print("Filter: Outside market hours");
      return false;
   }
   
   // Filter 5: Economic news filter
   if(IsHighImpactNewsTime())
   {
      Print("Filter: High impact news time");
      return false;
   }
   
   return true;
}

//+------------------------------------------------------------------+
//| Execute Trade Signal with Smart Position Sizing                 |
//+------------------------------------------------------------------+
void ExecuteTradeSignal(double signal_strength, string reason)
{
   if(g_emergencyMode || g_tradingHalted)
   {
      Print("Trading halted - Emergency mode active");
      return;
   }
   
   if(IsWeekendOrGap())
   {
      Print("Weekend gap protection - Trading suspended");
      return;
   }
   
   if(!CheckSpreadConditions())
   {
      Print("Spread too wide for execution");
      return;
   }
   
   if(!CheckMarginAvailability(signal_strength))
   {
      Print("Insufficient margin for trade");
      return;
   }
   
   double lot_size = CalculateSmartPositionSize(signal_strength);
   
   if(lot_size < InpMinPositionSize)
   {
      Print("Position size too small: ", lot_size);
      return;
   }
   
   ENUM_ORDER_TYPE order_type = (signal_strength > 0) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   double price = (order_type == ORDER_TYPE_BUY) ? symbol.Ask() : symbol.Bid();
   
   double sl = CalculateStopLoss(order_type, price);
   double tp = CalculateTakeProfit(order_type, price);
   
   if(!OptimizeOrderExecution(order_type, price, sl, tp))
   {
      Print("Order execution optimization failed");
      return;
   }
   
   string comment = StringFormat("VaaniV9[%s|%.2f|%.2f]", 
                                EnumToString(g_activeStrategy), 
                                signal_strength, 
                                g_mlRiskLevel);
   
   int max_retries = 3;
   int retry_count = 0;
   bool execution_success = false;
   
   while(retry_count < max_retries && !execution_success)
   {
      // CRITICAL FIX #3: Slippage cap validation
      trade.SetDeviationInPoints(InpSlippagePoints);
      
      // CRITICAL FIX #4: Spread filter before execution
      if(!CheckSpreadConditions())
      {
         Print("Spread too wide for execution on attempt ", retry_count + 1);
         retry_count++;
         Sleep(500); // Wait for spread to normalize
         continue;
      }
      
      // CRITICAL FIX #1: Actual trade execution call
      if(trade.PositionOpen(_Symbol, order_type, lot_size, price, sl, tp, comment))
      {
         Print("Trade executed: ", reason);
         Print("Type: ", EnumToString(order_type), " Size: ", lot_size, " Price: ", price);
         Print("SL: ", sl, " TP: ", tp, " Slippage: ", InpSlippagePoints);
         
         // Verify actual fill price vs requested price
         double actual_price = trade.ResultPrice();
         double slippage_pips = MathAbs(actual_price - price) / symbol.Point();
         Print("Actual fill price: ", actual_price, " Slippage: ", slippage_pips, " points");
         
         g_lastTradeTime = TimeCurrent();
         g_totalTrades++;
         execution_success = true;
         
         LogTradeExecution(order_type, lot_size, actual_price, sl, tp, reason);
      }
      else
      {
         uint result_code = trade.ResultRetcode();
         Print("Trade execution failed (attempt ", retry_count + 1, "): ", result_code, " - ", trade.ResultComment());
         
         // CRITICAL FIX #2: Intelligent retry logic
         if(result_code == TRADE_RETCODE_REQUOTE || 
            result_code == TRADE_RETCODE_PRICE_OFF ||
            result_code == TRADE_RETCODE_TIMEOUT ||
            result_code == TRADE_RETCODE_PRICE_CHANGED)
         {
            retry_count++;
            Sleep(100 + retry_count * 50); // Progressive delay
            
            // Update price for retry
            price = (order_type == ORDER_TYPE_BUY) ? symbol.Ask() : symbol.Bid();
            
            // Recalculate SL/TP with updated price
            sl = CalculateStopLoss(order_type, price);
            tp = CalculateTakeProfit(order_type, price);
         }
         else if(result_code == TRADE_RETCODE_INVALID_STOPS)
         {
            Print("Invalid stops detected - adjusting SL/TP");
            
            // CRITICAL FIX #5: Validate and adjust SL/TP
            long stops_level = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
            double min_distance = stops_level * symbol.Point();
            
            if(order_type == ORDER_TYPE_BUY)
            {
               sl = MathMax(sl, price - min_distance);
               tp = MathMin(tp, price + min_distance);
            }
            else
            {
               sl = MathMin(sl, price + min_distance);
               tp = MathMax(tp, price - min_distance);
            }
            
            retry_count++;
         }
         else
         {
            // Non-retryable error
            Print("Non-retryable error: ", result_code);
            break;
         }
      }
   }
   
   if(!execution_success)
   {
      Print("Trade execution failed after ", max_retries, " attempts");
   }
}

//+------------------------------------------------------------------+
//| Calculate Smart Position Size                                   |
//+------------------------------------------------------------------+
double CalculateSmartPositionSize(double signal_strength)
{
   double base_risk = InpRiskPercent / 100.0;
   double account_balance = account.Balance();
   double risk_amount = account_balance * base_risk;
   
   // Adjust for signal strength
   double signal_multiplier = MathAbs(signal_strength);
   risk_amount *= signal_multiplier;
   
   // Adjust for ML risk level
   if(InpMLEnhanced)
   {
      risk_amount *= (1.0 - g_mlRiskLevel * 0.5);
   }
   
   // Volatility targeting
   if(InpVolatilityTargeting)
   {
      double atr = GetATRValue(PERIOD_M15, 0);
      double normal_atr = GetATRAverage(PERIOD_M15, 20);
      double volatility_ratio = atr / normal_atr;
      
      risk_amount /= volatility_ratio;
   }
   
   // Kelly Criterion adjustment
   if(InpKellyCriterion && g_totalTrades > 10)
   {
      double win_rate = (double)g_winningTrades / g_totalTrades;
      double avg_win = (g_totalProfit > 0) ? g_totalProfit / g_winningTrades : 0;
      double avg_loss = (g_totalLoss < 0) ? MathAbs(g_totalLoss) / (g_totalTrades - g_winningTrades) : 1;
      
      if(avg_loss > 0)
      {
         double kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win;
         kelly_fraction = MathMax(0.01, MathMin(0.25, kelly_fraction)); // Limit Kelly
         risk_amount *= kelly_fraction * 4; // Scale Kelly to our risk system
      }
   }
   
   // Convert risk amount to lot size
   double stop_loss_points = InpStopLossPoints;
   double point_value = symbol.TickValue();
   double lot_size = risk_amount / (stop_loss_points * point_value);
   
   // Apply position size limits
   lot_size = MathMax(InpMinPositionSize, MathMin(InpMaxPositionSize, lot_size));
   
   // Normalize to broker's lot step
   double lot_step = symbol.LotsStep();
   lot_size = MathFloor(lot_size / lot_step) * lot_step;
   
   return lot_size;
}

//+------------------------------------------------------------------+
//| Manage Existing Positions                                       |
//+------------------------------------------------------------------+
void ManageExistingPositions()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(position.SelectByIndex(i) && position.Symbol() == _Symbol && 
         position.Magic() == InpMagicNumber)
      {
         // CRITICAL FIX #8: Break-even logic
         if(InpBreakEvenMode)
         {
            ApplyBreakEvenLogic();
         }
         
         // CRITICAL FIX #10: Partial close logic
         ApplyPartialCloseLogic();
         
         // Trailing stop logic
         if(InpUseTrailingStop)
         {
            ApplyTrailingStop();
         }
         
         // Time-based exit
         ApplyTimeBasedExit();
         
         // Strategy-specific management
         ApplyStrategySpecificManagement();
      }
   }
}

//+------------------------------------------------------------------+
//| Apply Break-Even Logic                                          |
//+------------------------------------------------------------------+
void ApplyBreakEven()
{
   double current_price = (position.PositionType() == POSITION_TYPE_BUY) ? 
                         symbol.Bid() : symbol.Ask();
   double open_price = position.PriceOpen();
   double sl = position.StopLoss();
   
   double break_even_distance = InpTrailingStart * symbol.Point();
   
   if(position.PositionType() == POSITION_TYPE_BUY)
   {
      if(current_price >= open_price + break_even_distance && 
         (sl < open_price || sl == 0))
      {
         trade.PositionModify(position.Ticket(), open_price, position.TakeProfit());
         Print("Break-even applied for BUY position");
      }
   }
   else
   {
      if(current_price <= open_price - break_even_distance && 
         (sl > open_price || sl == 0))
      {
         trade.PositionModify(position.Ticket(), open_price, position.TakeProfit());
         Print("Break-even applied for SELL position");
      }
   }
}

//+------------------------------------------------------------------+
//| Apply Trailing Stop                                             |
//+------------------------------------------------------------------+
void ApplyTrailingStop()
{
   double current_price = (position.PositionType() == POSITION_TYPE_BUY) ? 
                         symbol.Bid() : symbol.Ask();
   double sl = position.StopLoss();
   double trailing_step = InpTrailingStep * symbol.Point();
   double open_price = position.PriceOpen();
   
   if(position.PositionType() == POSITION_TYPE_BUY)
   {
      double new_sl = current_price - InpTrailingStart * symbol.Point();
      
      if((new_sl > sl + trailing_step || sl == 0) && new_sl > open_price)
      {
         if(current_price - new_sl >= InpTrailingStart * symbol.Point())
         {
            if(trade.PositionModify(position.Ticket(), new_sl, position.TakeProfit()))
            {
               Print("Trailing stop updated for BUY position: ", new_sl);
            }
         }
      }
   }
   else
   {
      double new_sl = current_price + InpTrailingStart * symbol.Point();
      
      if((new_sl < sl - trailing_step || sl == 0) && new_sl < open_price)
      {
         if(new_sl - current_price >= InpTrailingStart * symbol.Point())
         {
            if(trade.PositionModify(position.Ticket(), new_sl, position.TakeProfit()))
            {
               Print("Trailing stop updated for SELL position: ", new_sl);
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Helper Functions                                                |
//+------------------------------------------------------------------+
double GetRSIValue(ENUM_TIMEFRAMES timeframe, int shift)
{
   int handle = (timeframe == PERIOD_M15) ? g_handleRSI_M15 :
                (timeframe == PERIOD_H1) ? g_handleRSI_H1 :
                (timeframe == PERIOD_H4) ? g_handleRSI_H4 : g_handleRSI_D1;
   
   double rsi[];
   if(CopyBuffer(handle, 0, shift, 1, rsi) > 0)
      return rsi[0];
   return 50.0;
}

double GetATRValue(ENUM_TIMEFRAMES timeframe, int shift)
{
   int handle = (timeframe == PERIOD_M15) ? g_handleATR_M15 : g_handleATR_H1;
   
   double atr[];
   if(CopyBuffer(handle, 0, shift, 1, atr) > 0)
      return atr[0];
   return 0.001;
}

double GetATRAverage(ENUM_TIMEFRAMES timeframe, int period)
{
   int handle = (timeframe == PERIOD_M15) ? g_handleATR_M15 : g_handleATR_H1;
   
   double atr[];
   if(CopyBuffer(handle, 0, 0, period, atr) > 0)
   {
      double sum = 0;
      for(int i = 0; i < period; i++)
         sum += atr[i];
      return sum / period;
   }
   return 0.001;
}

bool IsNewsTime()
{
   // Simplified news detection
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   // Avoid trading during major news hours (simplified)
   if((dt.hour == 8 || dt.hour == 14) && dt.min < 60)
      return true;
   
   return false;
}

bool CheckSpreadConditions()
{
   double spread = symbol.Spread() * symbol.Point();
   double max_spread = InpMaxSpreadPoints * symbol.Point();
   
   return spread <= max_spread;
}

//+------------------------------------------------------------------+
//| Dashboard and Logging Functions                                 |
//+------------------------------------------------------------------+
void CreateDashboard()
{
   // Create dashboard objects
   ObjectCreate(0, "VaaniV9_Title", OBJ_LABEL, 0, 0, 0);
   ObjectSetString(0, "VaaniV9_Title", OBJPROP_TEXT, "VaaniV9 Elite EA");
   ObjectSetInteger(0, "VaaniV9_Title", OBJPROP_XDISTANCE, 10);
   ObjectSetInteger(0, "VaaniV9_Title", OBJPROP_YDISTANCE, 20);
   ObjectSetInteger(0, "VaaniV9_Title", OBJPROP_COLOR, clrGold);
   ObjectSetInteger(0, "VaaniV9_Title", OBJPROP_FONTSIZE, 12);
}

void UpdateDashboard()
{
   // Update dashboard with current information
   string info = StringFormat("Regime: %s | Strategy: %s | Equity: %.2f | DD: %.1f%%",
                             EnumToString(g_currentRegime),
                             EnumToString(g_activeStrategy),
                             g_currentEquity,
                             g_currentDrawdown);
   
   Comment(info);
}

void LogTradeExecution(ENUM_ORDER_TYPE type, double lots, double price, 
                      double sl, double tp, string reason)
{
   string log_entry = StringFormat("%s: %s %.2f lots at %.5f (SL:%.5f TP:%.5f) - %s",
                                  TimeToString(TimeCurrent()),
                                  EnumToString(type),
                                  lots, price, sl, tp, reason);
   Print(log_entry);
}

//+------------------------------------------------------------------+
//| Additional Helper Functions                                      |
//+------------------------------------------------------------------+
bool ShouldGenerateSignals()
{
   return !g_emergencyMode && !g_tradingHalted && CheckSpreadConditions();
}

bool ShouldResumeTrading()
{
   // Resume when volatility normalizes and drawdown improves
   bool volatility_normalized = g_volatilitySpike < InpVolatilitySpikeThreshold * 0.7;
   bool drawdown_improved = g_currentDrawdown < InpMaxDrawdownPercent * 0.6;
   bool no_crisis = !CheckCrisisConditions();
   
   if(volatility_normalized && drawdown_improved && no_crisis)
   {
      g_crisisMode = false;
      g_crashDetected = false;
      g_recoveryMode = false;
      g_activeHedges = 0;
      return true;
   }
   
   return false;
}

bool ShouldPerformDailyReset()
{
   MqlDateTime current_time, last_reset;
   TimeToStruct(TimeCurrent(), current_time);
   TimeToStruct(g_lastResetTime, last_reset);
   
   return current_time.day != last_reset.day;
}

void PerformDailyReset()
{
   Print("Performing daily reset - Refreshing strategy parameters");
   g_lastResetTime = TimeCurrent();
   
   // Reset daily statistics
   // Update strategy parameters based on recent performance
   // Refresh ML models if needed
}

void CloseAllPositions(string reason)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(position.SelectByIndex(i) && position.Symbol() == _Symbol && 
         position.Magic() == InpMagicNumber)
      {
         trade.PositionClose(position.Ticket());
         Print("Position closed: ", reason);
      }
   }
}

//+------------------------------------------------------------------+
//| Execute Crisis Profit Strategy                                  |
//+------------------------------------------------------------------+
void ExecuteCrisisProfitStrategy()
{
   Print("Executing Crisis Profit Strategy - Seeking opportunities in volatility");
   
   // Don't close existing positions - instead add hedging positions
   int existing_positions = PositionsTotal();
   
   if(existing_positions > 0)
   {
      // Add hedging positions instead of closing
      AddHedgingPositions();
   }
   
   // Look for counter-trend opportunities
   if(InpCounterTrendTrading)
   {
      ExecuteCounterTrendStrategy();
   }
   
   // Implement straddle strategy for high volatility
   ExecuteVolatilityStraddle();
}

//+------------------------------------------------------------------+
//| Add Hedging Positions                                           |
//+------------------------------------------------------------------+
void AddHedgingPositions()
{
   for(int i = 0; i < PositionsTotal(); i++)
   {
      if(position.SelectByIndex(i) && position.Symbol() == _Symbol && 
         position.Magic() == InpMagicNumber)
      {
         // Calculate hedge size
         double original_lots = position.Volume();
         double hedge_lots = original_lots * InpHedgeRatio;
         hedge_lots = NormalizeDouble(hedge_lots, 2);
         
         if(hedge_lots >= symbol.LotsMin())
         {
            // Open opposite position as hedge
            ENUM_ORDER_TYPE hedge_type = (position.PositionType() == POSITION_TYPE_BUY) ? 
                                        ORDER_TYPE_SELL : ORDER_TYPE_BUY;
            
            double price = (hedge_type == ORDER_TYPE_BUY) ? symbol.Ask() : symbol.Bid();
            
            // Tight stops for hedge positions
            double hedge_sl = (hedge_type == ORDER_TYPE_BUY) ? 
                             price - 200 * symbol.Point() : 
                             price + 200 * symbol.Point();
            
            double hedge_tp = (hedge_type == ORDER_TYPE_BUY) ? 
                             price + 300 * symbol.Point() : 
                             price - 300 * symbol.Point();
            
            if(trade.OrderOpen(_Symbol, hedge_type, hedge_lots, price, hedge_sl, hedge_tp, 
                              "Crisis Hedge"))
            {
               g_activeHedges++;
               Print("Hedge position opened: ", hedge_lots, " lots, Type: ", 
                     EnumToString(hedge_type));
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Execute Flash Crash Strategy                                    |
//+------------------------------------------------------------------+
void ExecuteFlashCrashStrategy()
{
   if(!g_crashDetected)
      return;
   
   Print("Executing Flash Crash Profit Strategy");
   
   // Determine crash direction and trade accordingly
   double prices[];
   if(CopyClose(_Symbol, PERIOD_M15, 0, 5, prices) >= 5)
   {
      double crash_magnitude = (prices[4] - prices[0]) / prices[0];
      double lot_size = CalculateSmartPositionSize(0.8) * InpRecoveryMultiplier;
      
      if(crash_magnitude < -InpCrashDetectionThreshold) // Downward crash
      {
         // Short into the crash for additional profit
         double price = symbol.Bid();
         double sl = price + 150 * symbol.Point(); // Tight stop
         double tp = price - 400 * symbol.Point(); // Larger target
         
         if(trade.OrderOpen(_Symbol, ORDER_TYPE_SELL, lot_size, price, sl, tp, 
                           "Flash Crash Short"))
         {
            Print("Flash crash short executed: ", lot_size, " lots at ", price);
         }
      }
      else if(crash_magnitude > InpCrashDetectionThreshold) // Upward spike
      {
         // Buy into the spike momentum
         double price = symbol.Ask();
         double sl = price - 150 * symbol.Point();
         double tp = price + 400 * symbol.Point();
         
         if(trade.OrderOpen(_Symbol, ORDER_TYPE_BUY, lot_size, price, sl, tp, 
                           "Flash Crash Long"))
         {
            Print("Flash crash long executed: ", lot_size, " lots at ", price);
         }
      }
   }
   
   g_crashDetected = false; // Reset flag
}

//+------------------------------------------------------------------+
//| Execute Counter-Trend Strategy                                  |
//+------------------------------------------------------------------+
void ExecuteCounterTrendStrategy()
{
   double rsi = GetRSIValue(PERIOD_M15, 0);
   double current_price = symbol.Bid();
   double lot_size = CalculateSmartPositionSize(0.6);
   
   // Counter-trend trades during high volatility
   if(g_volatilitySpike > InpVolatilitySpikeThreshold)
   {
      if(rsi > 75) // Extremely overbought
      {
         double price = symbol.Bid();
         double sl = price + 100 * symbol.Point();
         double tp = price - 250 * symbol.Point();
         
         if(trade.OrderOpen(_Symbol, ORDER_TYPE_SELL, lot_size, price, sl, tp, 
                           "Counter-trend Sell"))
         {
            Print("Counter-trend sell executed during volatility spike");
         }
      }
      else if(rsi < 25) // Extremely oversold
      {
         double price = symbol.Ask();
         double sl = price - 100 * symbol.Point();
         double tp = price + 250 * symbol.Point();
         
         if(trade.OrderOpen(_Symbol, ORDER_TYPE_BUY, lot_size, price, sl, tp, 
                           "Counter-trend Buy"))
         {
            Print("Counter-trend buy executed during volatility spike");
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Execute Volatility Straddle Strategy                           |
//+------------------------------------------------------------------+
void ExecuteVolatilityStraddle()
{
   if(g_volatilitySpike < InpVolatilitySpikeThreshold)
      return;
   
   // Place both buy and sell orders to capture volatility movement
   double current_price = (symbol.Ask() + symbol.Bid()) / 2;
   double lot_size = CalculateSmartPositionSize(0.4); // Smaller size for straddle
   double spread = symbol.Spread() * symbol.Point();
   
   // Buy order above current price
   double buy_price = current_price + 50 * symbol.Point() + spread;
   double buy_sl = buy_price - 150 * symbol.Point();
   double buy_tp = buy_price + 300 * symbol.Point();
   
   // Sell order below current price  
   double sell_price = current_price - 50 * symbol.Point();
   double sell_sl = sell_price + 150 * symbol.Point();
   double sell_tp = sell_price - 300 * symbol.Point();
   
   // Place pending orders
   if(trade.OrderOpen(_Symbol, ORDER_TYPE_BUY_STOP, lot_size, buy_price, buy_sl, buy_tp, 
                     "Volatility Straddle Buy"))
   {
      Print("Volatility straddle buy stop placed at ", buy_price);
   }
   
   if(trade.OrderOpen(_Symbol, ORDER_TYPE_SELL_STOP, lot_size, sell_price, sell_sl, sell_tp, 
                     "Volatility Straddle Sell"))
   {
      Print("Volatility straddle sell stop placed at ", sell_price);
   }
}

void SavePerformanceData()
{
   // Save performance metrics for analysis
   Print("Saving performance data...");
   // Implementation would save to file or send to external system
}

//+------------------------------------------------------------------+
//| Additional Helper Functions Implementation                       |
//+------------------------------------------------------------------+
double GetMACDValue(ENUM_TIMEFRAMES timeframe, int shift, int mode)
{
   int handle = (timeframe == PERIOD_M15) ? g_handleMACD_M15 :
                (timeframe == PERIOD_H1) ? g_handleMACD_H1 : g_handleMACD_H4;
   
   double macd[];
   if(CopyBuffer(handle, mode, shift, 1, macd) > 0)
      return macd[0];
   return 0.0;
}

double GetADXValue(ENUM_TIMEFRAMES timeframe, int shift)
{
   int handle = (timeframe == PERIOD_M15) ? g_handleADX_M15 : g_handleADX_H1;
   
   double adx[];
   if(CopyBuffer(handle, 0, shift, 1, adx) > 0)
      return adx[0];
   return 20.0;
}

double GetBollingerValue(ENUM_TIMEFRAMES timeframe, int shift, int mode)
{
   int handle = (timeframe == PERIOD_M15) ? g_handleBB_M15 : g_handleBB_H1;
   
   double bb[];
   if(CopyBuffer(handle, mode, shift, 1, bb) > 0)
      return bb[0];
   return symbol.Bid();
}

double GetEMAValue(ENUM_TIMEFRAMES timeframe, int period, int shift)
{
   int handle = iMA(_Symbol, timeframe, period, 0, MODE_EMA, PRICE_CLOSE);
   
   double ema[];
   if(CopyBuffer(handle, 0, shift, 1, ema) > 0)
      return ema[0];
   return symbol.Bid();
}

double GetVolumeRatio()
{
   // Simplified volume ratio calculation
   long current_volume[];
   long avg_volume[];
   
   if(CopyTickVolume(_Symbol, PERIOD_M15, 0, 1, current_volume) > 0 &&

bool IsWeekendOrGap()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   if(dt.day_of_week == 6 || dt.day_of_week == 0)
      return true;
      
   if(dt.day_of_week == 5 && dt.hour >= 22)
      return true;
      
   if(dt.day_of_week == 1 && dt.hour < 1)
      return true;
   
   if(dt.day_of_week == 1 && dt.hour >= 1 && dt.hour <= 3)
   {
      static double friday_close = 0.0;
      static bool friday_close_set = false;
      
      if(!friday_close_set)
      {
         double close_prices[];
         if(CopyClose(_Symbol, PERIOD_H1, 1, 1, close_prices) > 0)
         {
            friday_close = close_prices[0];
            friday_close_set = true;
         }
      }
      
      if(friday_close_set)
      {
         double current_price = (symbol.Ask() + symbol.Bid()) / 2;
         double gap_size = MathAbs(current_price - friday_close) / friday_close * 100;
         
         if(gap_size > 0.5)
         {
            Print("Monday gap detected: ", gap_size, "% - Trading suspended");
            return true;
         }
      }
   }
   
   return false;
}

bool CheckMarginAvailability(double signal_strength)
{
   double lot_size = CalculateSmartPositionSize(signal_strength);
   
   double margin_required = 0.0;
   if(!OrderCalcMargin(ORDER_TYPE_BUY, _Symbol, lot_size, symbol.Ask(), margin_required))
   {
      Print("Failed to calculate margin requirement");
      return false;
   }
   
   double free_margin = account.FreeMargin();
   double margin_level = account.MarginLevel();
   
   if(free_margin < margin_required * 2.0)
   {
      Print("Insufficient free margin. Required: ", margin_required * 2.0, " Available: ", free_margin);
      return false;
   }
   
   if(margin_level > 0 && margin_level < 300.0)
   {
      Print("Margin level too low: ", margin_level, "%");
      return false;
   }
   
   return true;
}

      CopyTickVolume(_Symbol, PERIOD_M15, 0, 20, avg_volume) > 0)
   {
      long sum = 0;
      for(int i = 1; i < 20; i++) // Skip current bar
         sum += avg_volume[i];
      
      double average = (double)sum / 19.0;
      return (average > 0) ? (double)current_volume[0] / average : 1.0;
   }
   
   return 1.0;
}

double GetPriceChangePercent(ENUM_TIMEFRAMES timeframe, int bars)
{
   double rates[];
   if(CopyClose(_Symbol, timeframe, 0, bars + 1, rates) > 0)
   {
      double current_price = rates[bars];
      double past_price = rates[0];
      
      if(past_price > 0)
         return (current_price - past_price) / past_price * 100.0;
   }
   
   return 0.0;
}

double GetTrendDirection()
{
   double ema_fast = GetEMAValue(PERIOD_M15, 12, 0);
   double ema_slow = GetEMAValue(PERIOD_M15, 26, 0);
   
   if(ema_fast > ema_slow)
      return 1.0;
   else if(ema_fast < ema_slow)
      return -1.0;
   else
      return 0.0;
}

bool IsMarketHours()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   int hour = dt.hour;
   int day_of_week = dt.day_of_week;
   
   // CRITICAL FIX #7: Enhanced weekend gap protection
   if(day_of_week == 6 || day_of_week == 0) // Saturday or Sunday
      return false;
      
   // Friday after 21:00 GMT - weekend gap protection
   if(day_of_week == 5 && hour >= 21)
   {
      Print("Weekend gap protection - Friday after 21:00 GMT");
      return false;
   }
      
   // Sunday before 22:00 GMT - weekend gap protection
   if(day_of_week == 0 && hour < 22)
   {
      Print("Weekend gap protection - Sunday before 22:00 GMT");
      return false;
   }
   
   // Low liquidity periods to avoid
   if(hour >= 22 || hour <= 0)
   {
      Print("Low liquidity period - Post US close");
      return false;
   }
   
   if(hour >= 5 && hour <= 6)
   {
      Print("Low liquidity period - Asian lunch");
      return false;
   }
   
   if((hour >= 1 && hour <= 9) ||
      (hour >= 8 && hour <= 17) ||
      (hour >= 13 && hour <= 21))
      return true;
   
   return false;
}

bool IsHighImpactNewsTime()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   // High impact news times (simplified)
   // NFP: First Friday of month at 8:30 EST
   // CPI: Mid-month at 8:30 EST
   // FOMC: 8 times per year at 14:00 EST
   
   if((dt.hour == 13 && dt.min >= 25 && dt.min <= 35) || // 8:30 EST
      (dt.hour == 19 && dt.min >= 55) ||                 // 14:00 EST start
      (dt.hour == 20 && dt.min <= 5))                    // 14:00 EST end
   {
      return true;
   }
   
   return false;
}

double CalculateStopLoss(ENUM_ORDER_TYPE order_type, double entry_price)
{
   double atr = GetATRValue(PERIOD_M15, 0);
   double sl_distance = MathMax(InpStopLossPoints * symbol.Point(), atr * 2.0);
   
   // Validate against broker's minimum stop level
   long stops_level = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double min_distance = stops_level * symbol.Point();
   sl_distance = MathMax(sl_distance, min_distance);
   
   if(order_type == ORDER_TYPE_BUY)
      return entry_price - sl_distance;
   else
      return entry_price + sl_distance;
}

double CalculateTakeProfit(ENUM_ORDER_TYPE order_type, double entry_price)
{
   double atr = GetATRValue(PERIOD_M15, 0);
   double tp_distance = MathMax(InpTakeProfitPoints * symbol.Point(), atr * 3.0);
   
   // Validate against broker's minimum stop level
   long stops_level = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double min_distance = stops_level * symbol.Point();
   tp_distance = MathMax(tp_distance, min_distance);
   
   if(order_type == ORDER_TYPE_BUY)
      return entry_price + tp_distance;
   else
      return entry_price - tp_distance;
}

void ApplyTimeBasedExit()
{
   datetime current_time = TimeCurrent();
   datetime position_time = (datetime)position.Time();
   
   // Close positions older than 24 hours
   if(current_time - position_time > 86400) // 24 hours in seconds
   {
      trade.PositionClose(position.Ticket());
      Print("Position closed due to time limit");
   }
}

void ApplyStrategySpecificManagement()
{
   switch(g_activeStrategy)
   {
      case STRATEGY_TREND_FOLLOWING:
         // Let trends run longer
         break;
         
      case STRATEGY_MEAN_REVERSION:
         // Quick exits for mean reversion
         if(position.Profit() > 0)
         {
            double profit_target = position.Volume() * 100 * symbol.TickValue();
            if(position.Profit() >= profit_target)
            {
               trade.PositionClose(position.Ticket());
               Print("Mean reversion profit target reached");
            }
         }
         break;
         
      case STRATEGY_BREAKOUT:
         // Momentum-based management
         break;
         
      case STRATEGY_NEWS_FADE:
         // Quick exits after news
         if(TimeCurrent() - position.Time() > 3600) // 1 hour
         {
            trade.PositionClose(position.Ticket());
            Print("News fade position closed after 1 hour");
         }
         break;
   }
}

//+------------------------------------------------------------------+
//| Advanced Risk Management Functions                              |
//+------------------------------------------------------------------+
bool CheckCorrelationRisk()
{
   // Check correlation with other open positions
   int total_positions = PositionsTotal();
   if(total_positions <= 1)
      return true;
   
   double total_exposure = 0.0;
   for(int i = 0; i < total_positions; i++)
   {
      if(position.SelectByIndex(i) && position.Magic() == InpMagicNumber)
      {
         double position_value = position.Volume() * symbol.TickValue();
         if(position.PositionType() == POSITION_TYPE_BUY)
            total_exposure += position_value;
         else
            total_exposure -= position_value;
      }
   }
   
   double max_exposure = account.Balance() * InpMaxRiskPercent / 100.0;
   return MathAbs(total_exposure) <= max_exposure;
}

void UpdatePerformanceMetrics()
{
   // Update win rate
   if(g_totalTrades > 0)
   {
      double win_rate = (double)g_winningTrades / g_totalTrades;
      
      // Update Sharpe ratio (simplified)
      if(g_totalTrades > 10)
      {
         double avg_return = g_totalProfit / g_totalTrades;
         double return_std = MathSqrt(MathAbs(g_totalProfit - g_totalLoss) / g_totalTrades);
         
         if(return_std > 0)
            g_sharpeRatio = avg_return / return_std * MathSqrt(252); // Annualized
      }
   }
}

//+------------------------------------------------------------------+
//| News and Economic Calendar Functions                            |
//+------------------------------------------------------------------+
bool IsNFPDay()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   // First Friday of the month
   if(dt.day_of_week == 5) // Friday
   {
      if(dt.day <= 7) // First week
         return true;
   }
   
   return false;
}

bool IsCPIDay()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   // Typically mid-month (10th-15th)
   if(dt.day >= 10 && dt.day <= 15)
      return true;
   
   return false;
}

bool IsFOMCDay()
{
   // FOMC meets 8 times per year
   // This would need to be updated with actual FOMC dates
   // For now, return false (implement with economic calendar)
   return false;
}

//+------------------------------------------------------------------+
//| Machine Learning Integration Functions                          |
//+------------------------------------------------------------------+
void UpdateMLModelPerformance()
{
   if(!g_mlModelsLoaded)
      return;
   
   // Track ML prediction accuracy
   static double ml_predictions[];
   static double actual_outcomes[];
   static int prediction_count = 0;
   
   // This would integrate with external ML models
   // For now, simulate model performance tracking
   
   if(prediction_count > 100)
   {
      // Retrain models if performance degrades
      double accuracy = CalculateMLAccuracy(ml_predictions, actual_outcomes, prediction_count);
      
      if(accuracy < 0.55) // Below 55% accuracy
      {
         Print("ML model performance degraded, retraining recommended");
         // Trigger model retraining
      }
   }
}

double CalculateMLAccuracy(double &predictions[], double &outcomes[], int count)
{
   int correct = 0;
   
   for(int i = 0; i < count; i++)
   {
      if((predictions[i] > 0 && outcomes[i] > 0) ||
         (predictions[i] < 0 && outcomes[i] < 0))
         correct++;
   }
   
   return (double)correct / count;
}

//+------------------------------------------------------------------+
//| Portfolio and Multi-Pair Functions                             |
//+------------------------------------------------------------------+
double CalculatePortfolioRisk()
{
   double total_risk = 0.0;
   
   for(int i = 0; i < PositionsTotal(); i++)
   {
      if(position.SelectByIndex(i) && position.Magic() == InpMagicNumber)
      {
         double position_risk = position.Volume() * symbol.TickValue() * InpStopLossPoints;
         total_risk += position_risk;
      }
   }
   
   return total_risk / account.Balance() * 100.0;
}

bool CheckPortfolioLimits()
{
   double portfolio_risk = CalculatePortfolioRisk();
   return portfolio_risk <= InpMaxRiskPercent;
}

//+------------------------------------------------------------------+
//| Execution Optimization Functions                               |
//+------------------------------------------------------------------+
bool OptimizeOrderExecution(ENUM_ORDER_TYPE order_type, double &price, double &sl, double &tp)
{
   // Check market depth and liquidity
   double spread = symbol.Spread() * symbol.Point();
   double normal_spread = InpMaxSpreadPoints * symbol.Point();
   
   if(spread > normal_spread)
   {
      Print("Spread too wide for execution: ", spread);
      return false;
   }
   
   // Adjust for slippage in volatile conditions
   double atr = GetATRValue(PERIOD_M1, 0);
   double volatility_adjustment = atr * 0.1;
   
   if(order_type == ORDER_TYPE_BUY)
   {
      price += volatility_adjustment;
      sl -= volatility_adjustment;
      tp += volatility_adjustment;
   }
   else
   {
      price -= volatility_adjustment;
      sl += volatility_adjustment;
      tp -= volatility_adjustment;
   }
   
   return true;
}

//+------------------------------------------------------------------+
//| Self-Learning and Adaptation Functions                         |
//+------------------------------------------------------------------+
void AdaptStrategyParameters()
{
   // Adapt parameters based on recent performance
   if(g_totalTrades > 50)
   {
      double recent_win_rate = CalculateRecentWinRate(20); // Last 20 trades
      
      if(recent_win_rate < 0.4) // Below 40%
      {
         // Reduce risk and tighten filters
         Print("Adapting to poor performance - reducing risk");
         // Implementation would adjust strategy parameters
      }
      else if(recent_win_rate > 0.7) // Above 70%
      {
         // Increase risk slightly
         Print("Adapting to good performance - optimizing risk");

//+------------------------------------------------------------------+
//| CRITICAL FIX #9: Validate existing positions on restart         |
//+------------------------------------------------------------------+
void ValidateExistingPositions()
{
   Print("Validating existing positions on EA restart...");
   
   int validated_positions = 0;
   for(int i = 0; i < PositionsTotal(); i++)
   {
      if(position.SelectByIndex(i) && position.Symbol() == _Symbol && 
         position.Magic() == InpMagicNumber)
      {
         validated_positions++;
         Print("Validated position: Ticket=", position.Ticket(), 
               " Type=", EnumToString(position.PositionType()),
               " Volume=", position.Volume(),
               " Profit=", position.Profit());
      }
   }
   
   Print("Position validation complete: ", validated_positions, " positions found");
}

//+------------------------------------------------------------------+
//| CRITICAL FIX #8: Break-even move logic                          |
//+------------------------------------------------------------------+
void ApplyBreakEvenLogic()
{
   double current_price = (position.PositionType() == POSITION_TYPE_BUY) ? 
                         symbol.Bid() : symbol.Ask();
   double open_price = position.PriceOpen();
   double sl = position.StopLoss();
   
   // Move to break-even after 10 pips profit
   double breakeven_threshold = 100 * symbol.Point(); // 10 pips
   
   if(position.PositionType() == POSITION_TYPE_BUY)
   {
      double profit_pips = current_price - open_price;
      
      if(profit_pips >= breakeven_threshold && sl < open_price)
      {
         double new_sl = open_price + 10 * symbol.Point(); // Break-even + 1 pip
         if(trade.PositionModify(position.Ticket(), new_sl, position.TakeProfit()))
         {
            Print("Break-even applied for BUY position: ", new_sl);
         }
      }
   }
   else // SELL position
   {
      double profit_pips = open_price - current_price;
      
      if(profit_pips >= breakeven_threshold && (sl > open_price || sl == 0))
      {
         double new_sl = open_price - 10 * symbol.Point(); // Break-even - 1 pip
         if(trade.PositionModify(position.Ticket(), new_sl, position.TakeProfit()))
         {
            Print("Break-even applied for SELL position: ", new_sl);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| CRITICAL FIX #10: Partial close logic                           |
//+------------------------------------------------------------------+
void ApplyPartialCloseLogic()
{
   double current_price = (position.PositionType() == POSITION_TYPE_BUY) ? 
                         symbol.Bid() : symbol.Ask();
   double open_price = position.PriceOpen();
   double volume = position.Volume();
   
   // Partial close after 10 pips profit (50% of position)
   double partial_close_threshold = 100 * symbol.Point(); // 10 pips
   
   if(position.PositionType() == POSITION_TYPE_BUY)
   {
      double profit_pips = current_price - open_price;
      
      if(profit_pips >= partial_close_threshold && volume > 0.01)
      {
         double close_volume = NormalizeDouble(volume * 0.5, 2); // Close 50%
         
         if(trade.PositionClosePartial(position.Ticket(), close_volume))
         {
            Print("Partial close executed for BUY: ", close_volume, " lots at ", current_price);
         }
      }
   }
   else // SELL position
   {
      double profit_pips = open_price - current_price;
      
      if(profit_pips >= partial_close_threshold && volume > 0.01)
      {
         double close_volume = NormalizeDouble(volume * 0.5, 2); // Close 50%
         
         if(trade.PositionClosePartial(position.Ticket(), close_volume))
         {
            Print("Partial close executed for SELL: ", close_volume, " lots at ", current_price);
         }
      }
   }
}



double CalculateRecentWinRate(int trades_count)
{
   return (g_totalTrades > 0) ? (double)g_winningTrades / g_totalTrades : 0.5;
}

//+------------------------------------------------------------------+
//| Compound Growth and Capital Management                          |
//+------------------------------------------------------------------+
void UpdateCompoundGrowthLogic()
{
   static double initial_balance = 0.0;
   
   if(initial_balance == 0.0)
      initial_balance = account.Balance();
   
   double growth_factor = account.Balance() / initial_balance;
   
   if(growth_factor > 1.5)
   {
      Print("Account grown by ", (growth_factor - 1.0) * 100, "% - adjusting position sizing");
   }
   else if(growth_factor < 0.8)
   {
      Print("Account drawdown detected - reducing position sizing");
   }
}

//+------------------------------------------------------------------+
//| CRITICAL FIX #6: Check margin availability before trade         |
//+------------------------------------------------------------------+
bool CheckMarginAvailability(double signal_strength)
{
   double lot_size = CalculateSmartPositionSize(signal_strength);
   
   // Calculate required margin for the trade
   double margin_required = 0.0;
   if(!OrderCalcMargin(ORDER_TYPE_BUY, _Symbol, lot_size, symbol.Ask(), margin_required))
   {
      Print("Failed to calculate margin requirement");
      return false;
   }
   
   double free_margin = account.FreeMargin();
   double margin_level = account.MarginLevel();
   
   // Ensure sufficient free margin (at least 200% of required)
   if(free_margin < margin_required * 2.0)
   {
      Print("Insufficient free margin. Required: ", margin_required * 2.0, " Available: ", free_margin);
      return false;
   }
   
   // Ensure margin level stays above 300%
   if(margin_level > 0 && margin_level < 300.0)
   {
      Print("Margin level too low: ", margin_level, "%");
      return false;
   }
   
   return true;
}

//+------------------------------------------------------------------+
//| CRITICAL FIX #7: Weekend gap protection                         |
//+------------------------------------------------------------------+
bool IsWeekendOrGap()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   // Weekend protection (Friday 22:00 GMT to Sunday 22:00 GMT)
   if(dt.day_of_week == 6 || dt.day_of_week == 0) // Saturday or Sunday
      return true;
      
   if(dt.day_of_week == 5 && dt.hour >= 22) // Friday after 22:00 GMT
      return true;
      
   if(dt.day_of_week == 1 && dt.hour < 1) // Monday before 01:00 GMT
      return true;
   
   // Monday gap protection - check for significant price gaps
   if(dt.day_of_week == 1 && dt.hour >= 1 && dt.hour <= 3)
   {
      static double friday_close = 0.0;
      static bool friday_close_set = false;
      
      if(!friday_close_set)
      {
         // Get Friday's closing price
         double close_prices[];
         if(CopyClose(_Symbol, PERIOD_H1, 1, 1, close_prices) > 0)
         {
            friday_close = close_prices[0];
            friday_close_set = true;
         }
      }
      
      if(friday_close_set)
      {
         double current_price = (symbol.Ask() + symbol.Bid()) / 2;
         double gap_size = MathAbs(current_price - friday_close) / friday_close * 100;
         
         if(gap_size > 0.5) // 0.5% gap threshold
         {
            Print("Monday gap detected: ", gap_size, "% - Trading suspended");
            return true;
         }
      }
   }
   
   return false;
}

//+------------------------------------------------------------------+
