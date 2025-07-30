#!/usr/bin/env python3
"""
Market Timing Agent - Analyzes optimal entry/exit timing for trades
Handles session analysis, volatility windows, temporal patterns
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, time
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass
import logging
from enum import Enum

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from Gremlin_Trade_Core.globals import logger, setup_module_logger

# Setup module logger
timing_logger = setup_module_logger("agents", "timing")

class MarketSession(Enum):
    PRE_MARKET = "pre_market"
    REGULAR = "regular"
    AFTER_HOURS = "after_hours"
    CLOSED = "closed"

@dataclass
class TimingSignal:
    symbol: str
    session: MarketSession
    optimal_entry: datetime
    optimal_exit: datetime
    volatility_window: str
    confidence: float
    reasoning: str

class MarketTimingAgent:
    """Analyzes market timing patterns and suggests optimal entry/exit points"""
    
    def __init__(self):
        self.session_times = {
            MarketSession.PRE_MARKET: (time(4, 0), time(9, 30)),
            MarketSession.REGULAR: (time(9, 30), time(16, 0)),
            MarketSession.AFTER_HOURS: (time(16, 0), time(20, 0)),
        }
        
        # Volatility patterns by session
        self.volatility_profiles = {
            MarketSession.PRE_MARKET: {"high": (4, 6), "medium": (6, 9)},
            MarketSession.REGULAR: {"high": (9.5, 11), "medium": (11, 15), "low": (15, 16)},
            MarketSession.AFTER_HOURS: {"medium": (16, 18), "low": (18, 20)}
        }
    
    def get_current_session(self) -> MarketSession:
        """Determine current market session"""
        now = datetime.now().time()
        
        for session, (start, end) in self.session_times.items():
            if start <= now <= end:
                return session
        
        return MarketSession.CLOSED
    
    def analyze_optimal_entry(self, symbol: str, strategy_type: str = "momentum") -> TimingSignal:
        """Analyze optimal entry timing for a symbol"""
        current_session = self.get_current_session()
        now = datetime.now()
        
        if strategy_type == "momentum":
            # Momentum strategies work best during high volatility windows
            if current_session == MarketSession.PRE_MARKET:
                optimal_entry = now + timedelta(minutes=30)  # Wait for volume buildup
                optimal_exit = now + timedelta(hours=1.5)    # Exit before regular hours
                volatility_window = "high"
                confidence = 0.75
                reasoning = "Pre-market momentum with volume confirmation"
                
            elif current_session == MarketSession.REGULAR:
                if now.time() < time(11, 0):  # Morning session
                    optimal_entry = now + timedelta(minutes=15)
                    optimal_exit = now + timedelta(hours=2)
                    volatility_window = "high"
                    confidence = 0.85
                    reasoning = "Regular hours opening momentum"
                else:  # Afternoon session
                    optimal_entry = now + timedelta(minutes=30)
                    optimal_exit = now + timedelta(hours=1)
                    volatility_window = "medium"
                    confidence = 0.65
                    reasoning = "Afternoon momentum with reduced volatility"
            
            else:  # After hours or closed
                optimal_entry = self._next_market_open() + timedelta(minutes=30)
                optimal_exit = optimal_entry + timedelta(hours=2)
                volatility_window = "high"
                confidence = 0.70
                reasoning = "Wait for next market open for momentum play"
        
        elif strategy_type == "mean_reversion":
            # Mean reversion works better during lower volatility periods
            if current_session == MarketSession.REGULAR and now.time() > time(14, 0):
                optimal_entry = now + timedelta(minutes=15)
                optimal_exit = now + timedelta(hours=1.5)
                volatility_window = "low"
                confidence = 0.80
                reasoning = "Late session mean reversion opportunity"
            else:
                optimal_entry = now + timedelta(hours=2)
                optimal_exit = optimal_entry + timedelta(hours=1)
                volatility_window = "medium"
                confidence = 0.60
                reasoning = "Wait for volatility to settle for mean reversion"
        
        else:  # Default/scalping
            optimal_entry = now + timedelta(minutes=10)
            optimal_exit = now + timedelta(minutes=45)
            volatility_window = "medium"
            confidence = 0.70
            reasoning = "Quick scalp during current session"
        
        return TimingSignal(
            symbol=symbol,
            session=current_session,
            optimal_entry=optimal_entry,
            optimal_exit=optimal_exit,
            volatility_window=volatility_window,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def analyze_volatility_window(self, symbol: str) -> Dict[str, float]:
        """Analyze current volatility conditions"""
        current_session = self.get_current_session()
        now = datetime.now()
        
        if current_session == MarketSession.CLOSED:
            return {"volatility_score": 0.0, "volume_score": 0.0, "timing_score": 0.0}
        
        # Simple volatility analysis based on session and time
        volatility_score = 0.0
        volume_score = 0.0
        timing_score = 0.0
        
        if current_session == MarketSession.PRE_MARKET:
            if 4 <= now.hour < 6:
                volatility_score = 0.9  # High volatility
                volume_score = 0.3      # Low volume
                timing_score = 0.6      # Decent timing
            elif 6 <= now.hour < 9:
                volatility_score = 0.7
                volume_score = 0.6
                timing_score = 0.8
        
        elif current_session == MarketSession.REGULAR:
            if 9.5 <= now.hour < 11:
                volatility_score = 0.95  # Highest volatility
                volume_score = 0.9       # High volume
                timing_score = 0.9       # Best timing
            elif 11 <= now.hour < 15:
                volatility_score = 0.6
                volume_score = 0.7
                timing_score = 0.7
            else:  # 15-16
                volatility_score = 0.8   # End of day volatility
                volume_score = 0.8
                timing_score = 0.75
        
        elif current_session == MarketSession.AFTER_HOURS:
            volatility_score = 0.4
            volume_score = 0.2
            timing_score = 0.3
        
        return {
            "volatility_score": volatility_score,
            "volume_score": volume_score,
            "timing_score": timing_score,
            "overall_score": (volatility_score + volume_score + timing_score) / 3
        }
    
    def get_session_analytics(self) -> Dict[str, any]:
        """Get comprehensive session analytics"""
        current_session = self.get_current_session()
        now = datetime.now()
        
        return {
            "current_session": current_session.value,
            "session_start": self._get_session_start(current_session),
            "session_end": self._get_session_end(current_session),
            "time_remaining": self._get_time_remaining_in_session(current_session),
            "next_session": self._get_next_session(current_session),
            "optimal_strategies": self._get_optimal_strategies_for_session(current_session),
            "volatility_forecast": self._forecast_volatility(current_session)
        }
    
    def _next_market_open(self) -> datetime:
        """Calculate next market open time"""
        now = datetime.now()
        next_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        
        if now.time() >= time(16, 0):  # After market close
            next_open += timedelta(days=1)
        
        # Handle weekends
        while next_open.weekday() > 4:  # Saturday = 5, Sunday = 6
            next_open += timedelta(days=1)
        
        return next_open
    
    def _get_session_start(self, session: MarketSession) -> Optional[datetime]:
        """Get session start time"""
        if session == MarketSession.CLOSED:
            return None
        
        now = datetime.now()
        start_time = self.session_times[session][0]
        return now.replace(hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0)
    
    def _get_session_end(self, session: MarketSession) -> Optional[datetime]:
        """Get session end time"""
        if session == MarketSession.CLOSED:
            return None
        
        now = datetime.now()
        end_time = self.session_times[session][1]
        return now.replace(hour=end_time.hour, minute=end_time.minute, second=0, microsecond=0)
    
    def _get_time_remaining_in_session(self, session: MarketSession) -> Optional[timedelta]:
        """Get time remaining in current session"""
        if session == MarketSession.CLOSED:
            return None
        
        session_end = self._get_session_end(session)
        return session_end - datetime.now()
    
    def _get_next_session(self, current_session: MarketSession) -> MarketSession:
        """Get next market session"""
        session_order = [
            MarketSession.PRE_MARKET,
            MarketSession.REGULAR,
            MarketSession.AFTER_HOURS,
            MarketSession.CLOSED
        ]
        
        if current_session == MarketSession.CLOSED:
            return MarketSession.PRE_MARKET
        
        try:
            current_index = session_order.index(current_session)
            return session_order[(current_index + 1) % len(session_order)]
        except ValueError:
            return MarketSession.PRE_MARKET
    
    def _get_optimal_strategies_for_session(self, session: MarketSession) -> List[str]:
        """Get optimal trading strategies for current session"""
        strategy_map = {
            MarketSession.PRE_MARKET: ["momentum", "gap_trading", "news_reaction"],
            MarketSession.REGULAR: ["momentum", "scalping", "swing_trading", "mean_reversion"],
            MarketSession.AFTER_HOURS: ["mean_reversion", "position_holding"],
            MarketSession.CLOSED: ["analysis", "planning", "research"]
        }
        
        return strategy_map.get(session, ["analysis"])
    
    def _forecast_volatility(self, session: MarketSession) -> Dict[str, float]:
        """Forecast volatility for different time horizons"""
        base_volatility = {
            MarketSession.PRE_MARKET: 0.7,
            MarketSession.REGULAR: 0.9,
            MarketSession.AFTER_HOURS: 0.4,
            MarketSession.CLOSED: 0.0
        }
        
        current_vol = base_volatility.get(session, 0.0)
        
        return {
            "current": current_vol,
            "15min": current_vol * 0.9,
            "1hour": current_vol * 0.8,
            "4hour": current_vol * 0.6,
            "daily": current_vol * 0.5
        }

# Main execution
if __name__ == "__main__":
    timing_agent = MarketTimingAgent()
    
    # Example usage
    signal = timing_agent.analyze_optimal_entry("AAPL", "momentum")
    print(f"Timing Signal for AAPL:")
    print(f"  Session: {signal.session.value}")
    print(f"  Optimal Entry: {signal.optimal_entry}")
    print(f"  Optimal Exit: {signal.optimal_exit}")
    print(f"  Volatility Window: {signal.volatility_window}")
    print(f"  Confidence: {signal.confidence:.2%}")
    print(f"  Reasoning: {signal.reasoning}")
    
    # Session analytics
    analytics = timing_agent.get_session_analytics()
    print(f"\nSession Analytics:")
    for key, value in analytics.items():
        print(f"  {key}: {value}")
