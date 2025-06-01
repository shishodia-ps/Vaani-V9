"""
Macro economic event agent for tracking and analyzing economic news and events
"""

import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

class EventImpact(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class EventType(Enum):
    INTEREST_RATE = "interest_rate"
    EMPLOYMENT = "employment"
    INFLATION = "inflation"
    GDP = "gdp"
    CENTRAL_BANK = "central_bank"
    TRADE = "trade"
    POLITICAL = "political"
    OTHER = "other"

@dataclass
class EconomicEvent:
    """Economic event data structure"""
    title: str
    country: str
    currency: str
    datetime: datetime
    impact: EventImpact
    event_type: EventType
    forecast: Optional[str] = None
    previous: Optional[str] = None
    actual: Optional[str] = None
    description: str = ""

class MacroEventAgent:
    """Tracks and analyzes macroeconomic events"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.events_cache: List[EconomicEvent] = []
        self.last_update = datetime.now() - timedelta(hours=1)
        self.update_interval = timedelta(hours=1)
        
        self.currency_impact_map = {
            'USD': ['NFP', 'CPI', 'FOMC', 'GDP', 'Unemployment'],
            'EUR': ['ECB', 'CPI', 'GDP', 'Unemployment', 'PMI'],
            'GBP': ['BOE', 'CPI', 'GDP', 'Employment', 'PMI'],
            'JPY': ['BOJ', 'CPI', 'GDP', 'Tankan'],
            'CHF': ['SNB', 'CPI', 'GDP'],
            'CAD': ['BOC', 'CPI', 'GDP', 'Employment'],
            'AUD': ['RBA', 'CPI', 'GDP', 'Employment'],
            'NZD': ['RBNZ', 'CPI', 'GDP']
        }
    
    def get_upcoming_events(self, hours_ahead: int = 24) -> List[EconomicEvent]:
        """Get upcoming economic events"""
        try:
            if datetime.now() - self.last_update > self.update_interval:
                self._update_events_cache()
            
            now = datetime.now()
            cutoff = now + timedelta(hours=hours_ahead)
            
            upcoming_events = [
                event for event in self.events_cache
                if now <= event.datetime <= cutoff
            ]
            
            upcoming_events.sort(key=lambda x: x.datetime)
            
            return upcoming_events
            
        except Exception as e:
            self.logger.error(f"Error getting upcoming events: {e}")
            return []
    
    def get_high_impact_events(self, hours_ahead: int = 24) -> List[EconomicEvent]:
        """Get high impact events only"""
        upcoming_events = self.get_upcoming_events(hours_ahead)
        return [event for event in upcoming_events if event.impact == EventImpact.HIGH]
    
    def analyze_event_impact(self, symbol: str, hours_ahead: int = 24) -> Dict[str, Any]:
        """Analyze potential impact of upcoming events on a currency pair"""
        try:
            if len(symbol) < 6:
                return {"error": "Invalid symbol format"}
            
            base_currency = symbol[:3]
            quote_currency = symbol[3:6]
            
            upcoming_events = self.get_upcoming_events(hours_ahead)
            
            relevant_events = []
            for event in upcoming_events:
                if event.currency in [base_currency, quote_currency]:
                    relevant_events.append(event)
            
            impact_analysis = {
                "symbol": symbol,
                "base_currency": base_currency,
                "quote_currency": quote_currency,
                "total_events": len(relevant_events),
                "high_impact_events": len([e for e in relevant_events if e.impact == EventImpact.HIGH]),
                "events": [self._event_to_dict(event) for event in relevant_events],
                "risk_assessment": self._assess_news_risk(relevant_events),
                "trading_recommendation": self._generate_trading_recommendation(relevant_events, symbol),
                "next_major_event": self._get_next_major_event(relevant_events)
            }
            
            return impact_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing event impact: {e}")
            return {"error": str(e)}
    
    def _update_events_cache(self):
        """Update the events cache from external sources"""
        try:
            self.events_cache = self._create_sample_events()
            self.last_update = datetime.now()
            self.logger.info("Events cache updated")
            
        except Exception as e:
            self.logger.error(f"Error updating events cache: {e}")
    
    def _create_sample_events(self) -> List[EconomicEvent]:
        """Create sample economic events for testing"""
        now = datetime.now()
        sample_events = []
        
        events_data = [
            {
                "title": "Non-Farm Payrolls",
                "country": "United States",
                "currency": "USD",
                "hours_offset": 2,
                "impact": EventImpact.HIGH,
                "event_type": EventType.EMPLOYMENT,
                "forecast": "200K",
                "previous": "180K"
            },
            {
                "title": "Consumer Price Index",
                "country": "Eurozone",
                "currency": "EUR",
                "hours_offset": 8,
                "impact": EventImpact.HIGH,
                "event_type": EventType.INFLATION,
                "forecast": "2.1%",
                "previous": "2.0%"
            },
            {
                "title": "Bank of England Rate Decision",
                "country": "United Kingdom",
                "currency": "GBP",
                "hours_offset": 12,
                "impact": EventImpact.HIGH,
                "event_type": EventType.INTEREST_RATE,
                "forecast": "5.25%",
                "previous": "5.25%"
            },
            {
                "title": "GDP Quarterly",
                "country": "Japan",
                "currency": "JPY",
                "hours_offset": 18,
                "impact": EventImpact.MEDIUM,
                "event_type": EventType.GDP,
                "forecast": "0.2%",
                "previous": "0.1%"
            },
            {
                "title": "Unemployment Rate",
                "country": "Canada",
                "currency": "CAD",
                "hours_offset": 30,
                "impact": EventImpact.MEDIUM,
                "event_type": EventType.EMPLOYMENT,
                "forecast": "6.1%",
                "previous": "6.2%"
            }
        ]
        
        for event_data in events_data:
            event = EconomicEvent(
                title=event_data["title"],
                country=event_data["country"],
                currency=event_data["currency"],
                datetime=now + timedelta(hours=event_data["hours_offset"]),
                impact=event_data["impact"],
                event_type=event_data["event_type"],
                forecast=event_data.get("forecast"),
                previous=event_data.get("previous"),
                description=f"{event_data['title']} for {event_data['country']}"
            )
            sample_events.append(event)
        
        return sample_events
    
    def _assess_news_risk(self, events: List[EconomicEvent]) -> str:
        """Assess overall news risk level"""
        if not events:
            return "low"
        
        high_impact_count = len([e for e in events if e.impact == EventImpact.HIGH])
        medium_impact_count = len([e for e in events if e.impact == EventImpact.MEDIUM])
        
        risk_score = high_impact_count * 3 + medium_impact_count * 1
        
        if risk_score >= 6:
            return "critical"
        elif risk_score >= 3:
            return "high"
        elif risk_score >= 1:
            return "medium"
        else:
            return "low"
    
    def _generate_trading_recommendation(self, events: List[EconomicEvent], symbol: str) -> str:
        """Generate trading recommendation based on upcoming events"""
        if not events:
            return "normal_trading"
        
        high_impact_events = [e for e in events if e.impact == EventImpact.HIGH]
        
        if len(high_impact_events) >= 2:
            return "avoid_trading"
        elif len(high_impact_events) == 1:
            next_event = min(events, key=lambda x: x.datetime)
            hours_until = (next_event.datetime - datetime.now()).total_seconds() / 3600
            
            if hours_until <= 4:
                return "reduce_position_size"
            else:
                return "cautious_trading"
        else:
            return "normal_trading"
    
    def _get_next_major_event(self, events: List[EconomicEvent]) -> Optional[Dict]:
        """Get the next major (high impact) event"""
        high_impact_events = [e for e in events if e.impact == EventImpact.HIGH]
        
        if high_impact_events:
            next_event = min(high_impact_events, key=lambda x: x.datetime)
            return self._event_to_dict(next_event)
        
        return None
    
    def _event_to_dict(self, event: EconomicEvent) -> Dict:
        """Convert event to dictionary"""
        return {
            "title": event.title,
            "country": event.country,
            "currency": event.currency,
            "datetime": event.datetime.isoformat(),
            "impact": event.impact.value,
            "event_type": event.event_type.value,
            "forecast": event.forecast,
            "previous": event.previous,
            "actual": event.actual,
            "description": event.description,
            "hours_until": (event.datetime - datetime.now()).total_seconds() / 3600
        }
    
    def get_currency_exposure_risk(self, positions: List[Dict]) -> Dict[str, Any]:
        """Analyze currency exposure risk based on upcoming events"""
        try:
            currency_exposure = {}
            for pos in positions:
                symbol = pos.get('symbol', '')
                if len(symbol) >= 6:
                    base = symbol[:3]
                    quote = symbol[3:6]
                    volume = pos.get('volume', 0)
                    
                    currency_exposure[base] = currency_exposure.get(base, 0) + volume
                    currency_exposure[quote] = currency_exposure.get(quote, 0) + volume
            
            high_impact_events = self.get_high_impact_events(48)
            
            currency_risks = {}
            for currency, exposure in currency_exposure.items():
                currency_events = [e for e in high_impact_events if e.currency == currency]
                
                if currency_events:
                    next_event = min(currency_events, key=lambda x: x.datetime)
                    hours_until = (next_event.datetime - datetime.now()).total_seconds() / 3600
                    
                    risk_level = "high" if hours_until <= 4 else "medium"
                    
                    currency_risks[currency] = {
                        "exposure": exposure,
                        "risk_level": risk_level,
                        "next_event": self._event_to_dict(next_event),
                        "total_events": len(currency_events)
                    }
                else:
                    currency_risks[currency] = {
                        "exposure": exposure,
                        "risk_level": "low",
                        "next_event": None,
                        "total_events": 0
                    }
            
            return {
                "currency_risks": currency_risks,
                "overall_risk": self._calculate_overall_exposure_risk(currency_risks),
                "recommendations": self._generate_exposure_recommendations(currency_risks)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing currency exposure risk: {e}")
            return {"error": str(e)}
    
    def _calculate_overall_exposure_risk(self, currency_risks: Dict) -> str:
        """Calculate overall exposure risk"""
        high_risk_currencies = len([c for c in currency_risks.values() if c['risk_level'] == 'high'])
        medium_risk_currencies = len([c for c in currency_risks.values() if c['risk_level'] == 'medium'])
        
        if high_risk_currencies >= 2:
            return "critical"
        elif high_risk_currencies >= 1:
            return "high"
        elif medium_risk_currencies >= 2:
            return "medium"
        else:
            return "low"
    
    def _generate_exposure_recommendations(self, currency_risks: Dict) -> List[str]:
        """Generate recommendations based on currency exposure risks"""
        recommendations = []
        
        for currency, risk_data in currency_risks.items():
            if risk_data['risk_level'] == 'high':
                recommendations.append(f"Consider reducing {currency} exposure before upcoming high-impact event")
            elif risk_data['risk_level'] == 'medium' and risk_data['exposure'] > 2:
                recommendations.append(f"Monitor {currency} positions closely due to upcoming events")
        
        if not recommendations:
            recommendations.append("Current currency exposure risk is manageable")
        
        return recommendations
    
    def get_news_calendar_summary(self, days_ahead: int = 7) -> Dict[str, Any]:
        """Get summary of economic calendar for specified days"""
        try:
            events = self.get_upcoming_events(days_ahead * 24)
            
            events_by_day = {}
            for event in events:
                day_key = event.datetime.strftime('%Y-%m-%d')
                if day_key not in events_by_day:
                    events_by_day[day_key] = []
                events_by_day[day_key].append(event)
            
            summary = {
                "total_events": len(events),
                "high_impact_events": len([e for e in events if e.impact == EventImpact.HIGH]),
                "events_by_day": {},
                "currencies_affected": list(set([e.currency for e in events])),
                "event_types": list(set([e.event_type.value for e in events]))
            }
            
            for day, day_events in events_by_day.items():
                summary["events_by_day"][day] = {
                    "total": len(day_events),
                    "high_impact": len([e for e in day_events if e.impact == EventImpact.HIGH]),
                    "events": [self._event_to_dict(e) for e in day_events]
                }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error creating calendar summary: {e}")
            return {"error": str(e)}
