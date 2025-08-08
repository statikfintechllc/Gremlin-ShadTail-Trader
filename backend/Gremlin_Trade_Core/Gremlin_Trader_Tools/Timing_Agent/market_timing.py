#!/usr/bin/env python3
"""
Market Timing Agent - Analyzes optimal entry/exit timing for trades
Handles session analysis, volatility windows, temporal patterns with memory-based learning
"""

# Import ALL dependencies through globals.py (required)
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from Gremlin_Trade_Core.globals import (
    # Core imports
    sys, os, datetime, timedelta, time, pd, np, logging, asyncio, json,
    # Type imports
    Dict, List, Tuple, Optional,
    # Additional imports
    dataclass, Enum,
    # Configuration and utilities
    logger, setup_module_logger
)

# Import base memory agent
from Gremlin_Trade_Core.Gremlin_Trader_Tools.Memory_Agent.base_memory_agent import BaseMemoryAgent

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
    expected_hold_time: timedelta
    risk_level: str

class MarketTimingAgent(BaseMemoryAgent):
    """Analyzes market timing patterns and suggests optimal entry/exit points with memory-based learning"""
    
    def __init__(self):
        super().__init__("MarketTimingAgent", "timing")
        
        self.session_times = {
            MarketSession.PRE_MARKET: (time(4, 0), time(9, 30)),
            MarketSession.REGULAR: (time(9, 30), time(16, 0)),
            MarketSession.AFTER_HOURS: (time(16, 0), time(20, 0)),
        }
        
        # Volatility patterns by session - learned from experience
        self.volatility_profiles = {
            MarketSession.PRE_MARKET: {"high": (4, 6), "medium": (6, 9)},
            MarketSession.REGULAR: {"high": (9.5, 11), "medium": (11, 15), "low": (15, 16)},
            MarketSession.AFTER_HOURS: {"medium": (16, 18), "low": (18, 20)}
        }
        
        # Performance tracking by session and strategy
        self.session_performance = {}
        self.strategy_performance = {}
        
        # Load historical timing patterns from memory
        self._load_timing_patterns()
        
        timing_logger.info("Market Timing Agent initialized with memory integration")
    
    def _load_timing_patterns(self):
        """Load learned timing patterns from memory"""
        try:
            # Retrieve past timing experiences
            timing_memories = self.retrieve_memories(
                query="timing signal performance session volatility",
                memory_type="timing_analysis",
                limit=100
            )
            
            # Analyze patterns from memories
            for memory in timing_memories:
                metadata = memory.get('metadata', {})
                session = metadata.get('session')
                strategy = metadata.get('strategy_type')
                success = metadata.get('success', False)
                
                if session:
                    if session not in self.session_performance:
                        self.session_performance[session] = {'total': 0, 'successful': 0}
                    self.session_performance[session]['total'] += 1
                    if success:
                        self.session_performance[session]['successful'] += 1
                
                if strategy:
                    if strategy not in self.strategy_performance:
                        self.strategy_performance[strategy] = {'total': 0, 'successful': 0}
                    self.strategy_performance[strategy]['total'] += 1
                    if success:
                        self.strategy_performance[strategy]['successful'] += 1
            
            self.logger.info(f"Loaded timing patterns from {len(timing_memories)} memories")
            
        except Exception as e:
            self.logger.error(f"Error loading timing patterns: {e}")
    
    def get_current_session(self) -> MarketSession:
        """Determine current market session"""
        now = datetime.now().time()
        
        for session, (start, end) in self.session_times.items():
            if start <= now <= end:
                return session
        
        return MarketSession.CLOSED
    
    async def analyze_optimal_entry(self, symbol: str, strategy_type: str = "momentum") -> TimingSignal:
        """Analyze optimal entry timing for a symbol with memory-enhanced decision making"""
        current_session = self.get_current_session()
        now = datetime.now()
        
        # Get historical performance for this strategy and session
        session_accuracy = self._get_session_accuracy(current_session)
        strategy_accuracy = self._get_strategy_accuracy(strategy_type)
        
        # Get similar past experiences
        situation_context = f"symbol:{symbol} session:{current_session.value} strategy:{strategy_type} time:{now.hour}"
        similar_experiences = self.get_similar_experiences(situation_context, limit=10)
        
        base_confidence = 0.5
        
        if strategy_type == "momentum":
            signal = self._analyze_momentum_timing(symbol, current_session, now)
            base_confidence = 0.75
        elif strategy_type == "mean_reversion":
            signal = self._analyze_mean_reversion_timing(symbol, current_session, now)
            base_confidence = 0.65
        elif strategy_type == "scalping":
            signal = self._analyze_scalping_timing(symbol, current_session, now)
            base_confidence = 0.70
        else:
            signal = self._analyze_default_timing(symbol, current_session, now)
            base_confidence = 0.60
        
        # Adjust confidence based on historical performance
        confidence_adjustments = []
        
        if session_accuracy > 0:
            session_adjustment = (session_accuracy - 0.5) * 0.3
            signal.confidence += session_adjustment
            confidence_adjustments.append(f"session_accuracy:{session_accuracy:.2%}")
        
        if strategy_accuracy > 0:
            strategy_adjustment = (strategy_accuracy - 0.5) * 0.3
            signal.confidence += strategy_adjustment
            confidence_adjustments.append(f"strategy_accuracy:{strategy_accuracy:.2%}")
        
        # Learn from similar experiences
        if similar_experiences:
            successful_similar = sum(1 for exp in similar_experiences 
                                   if exp['metadata'].get('success', False))
            similarity_accuracy = successful_similar / len(similar_experiences)
            
            similarity_adjustment = (similarity_accuracy - 0.5) * 0.2
            signal.confidence += similarity_adjustment
            confidence_adjustments.append(f"similar_experiences:{len(similar_experiences)} accuracy:{similarity_accuracy:.2%}")
        
        # Clamp confidence
        signal.confidence = max(0.1, min(0.95, signal.confidence))
        
        # Add memory-based reasoning
        if confidence_adjustments:
            signal.reasoning += f" | Memory adjustments: {', '.join(confidence_adjustments)}"
        
        # Store this timing analysis in memory
        await self._store_timing_analysis(signal, strategy_type, similar_experiences)
        
        return signal
    
    def _analyze_momentum_timing(self, symbol: str, session: MarketSession, now: datetime) -> TimingSignal:
        """Analyze momentum strategy timing"""
        if session == MarketSession.PRE_MARKET:
            optimal_entry = now + timedelta(minutes=30)
            optimal_exit = now + timedelta(hours=1.5)
            volatility_window = "high"
            confidence = 0.75
            reasoning = "Pre-market momentum with volume confirmation"
            risk_level = "medium"
            
        elif session == MarketSession.REGULAR:
            if now.time() < time(11, 0):
                optimal_entry = now + timedelta(minutes=15)
                optimal_exit = now + timedelta(hours=2)
                volatility_window = "high"
                confidence = 0.85
                reasoning = "Regular hours opening momentum"
                risk_level = "medium"
            else:
                optimal_entry = now + timedelta(minutes=30)
                optimal_exit = now + timedelta(hours=1)
                volatility_window = "medium"
                confidence = 0.65
                reasoning = "Afternoon momentum with reduced volatility"
                risk_level = "low"
        
        else:  # After hours or closed
            optimal_entry = self._next_market_open() + timedelta(minutes=30)
            optimal_exit = optimal_entry + timedelta(hours=2)
            volatility_window = "high"
            confidence = 0.70
            reasoning = "Wait for next market open for momentum play"
            risk_level = "medium"
        
        return TimingSignal(
            symbol=symbol,
            session=session,
            optimal_entry=optimal_entry,
            optimal_exit=optimal_exit,
            volatility_window=volatility_window,
            confidence=confidence,
            reasoning=reasoning,
            expected_hold_time=optimal_exit - optimal_entry,
            risk_level=risk_level
        )
    
    def _analyze_mean_reversion_timing(self, symbol: str, session: MarketSession, now: datetime) -> TimingSignal:
        """Analyze mean reversion strategy timing"""
        if session == MarketSession.REGULAR and now.time() > time(14, 0):
            optimal_entry = now + timedelta(minutes=15)
            optimal_exit = now + timedelta(hours=1.5)
            volatility_window = "low"
            confidence = 0.80
            reasoning = "Late session mean reversion opportunity"
            risk_level = "low"
        else:
            optimal_entry = now + timedelta(hours=2)
            optimal_exit = optimal_entry + timedelta(hours=1)
            volatility_window = "medium"
            confidence = 0.60
            reasoning = "Wait for volatility to settle for mean reversion"
            risk_level = "medium"
        
        return TimingSignal(
            symbol=symbol,
            session=session,
            optimal_entry=optimal_entry,
            optimal_exit=optimal_exit,
            volatility_window=volatility_window,
            confidence=confidence,
            reasoning=reasoning,
            expected_hold_time=optimal_exit - optimal_entry,
            risk_level=risk_level
        )
    
    def _analyze_scalping_timing(self, symbol: str, session: MarketSession, now: datetime) -> TimingSignal:
        """Analyze scalping strategy timing"""
        if session == MarketSession.REGULAR:
            optimal_entry = now + timedelta(minutes=5)
            optimal_exit = now + timedelta(minutes=30)
            volatility_window = "high"
            confidence = 0.75
            reasoning = "High-frequency scalping during regular hours"
            risk_level = "high"
        else:
            optimal_entry = now + timedelta(minutes=10)
            optimal_exit = now + timedelta(minutes=45)
            volatility_window = "medium"
            confidence = 0.60
            reasoning = "Extended scalp during off-hours"
            risk_level = "medium"
        
        return TimingSignal(
            symbol=symbol,
            session=session,
            optimal_entry=optimal_entry,
            optimal_exit=optimal_exit,
            volatility_window=volatility_window,
            confidence=confidence,
            reasoning=reasoning,
            expected_hold_time=optimal_exit - optimal_entry,
            risk_level=risk_level
        )
    
    def _analyze_default_timing(self, symbol: str, session: MarketSession, now: datetime) -> TimingSignal:
        """Default timing analysis"""
        optimal_entry = now + timedelta(minutes=10)
        optimal_exit = now + timedelta(minutes=45)
        volatility_window = "medium"
        confidence = 0.50
        reasoning = "Default timing strategy"
        risk_level = "medium"
        
        return TimingSignal(
            symbol=symbol,
            session=session,
            optimal_entry=optimal_entry,
            optimal_exit=optimal_exit,
            volatility_window=volatility_window,
            confidence=confidence,
            reasoning=reasoning,
            expected_hold_time=optimal_exit - optimal_entry,
            risk_level=risk_level
        )
    
    async def _store_timing_analysis(self, signal: TimingSignal, strategy_type: str, similar_experiences: List):
        """Store timing analysis in memory"""
        content = f"Timing analysis for {signal.symbol}: {strategy_type} strategy in {signal.session.value} session. Entry: {signal.optimal_entry}, Exit: {signal.optimal_exit}, Confidence: {signal.confidence:.2%}"
        
        metadata = {
            'symbol': signal.symbol,
            'strategy_type': strategy_type,
            'session': signal.session.value,
            'volatility_window': signal.volatility_window,
            'confidence': signal.confidence,
            'risk_level': signal.risk_level,
            'expected_hold_minutes': int(signal.expected_hold_time.total_seconds() / 60),
            'similar_experiences_count': len(similar_experiences),
            'market_hour': datetime.now().hour
        }
        
        self.store_memory(content, "timing_analysis", metadata)
    
    def _get_session_accuracy(self, session: MarketSession) -> float:
        """Get historical accuracy for this session"""
        session_data = self.session_performance.get(session.value, {})
        total = session_data.get('total', 0)
        successful = session_data.get('successful', 0)
        
        return successful / total if total > 0 else 0.0
    
    def _get_strategy_accuracy(self, strategy_type: str) -> float:
        """Get historical accuracy for this strategy"""
        strategy_data = self.strategy_performance.get(strategy_type, {})
        total = strategy_data.get('total', 0)
        successful = strategy_data.get('successful', 0)
        
        return successful / total if total > 0 else 0.0
    
    async def record_timing_outcome(self, symbol: str, strategy_type: str, entry_time: datetime, 
                                  exit_time: datetime, success: bool, profit_loss: float):
        """Record the outcome of a timing recommendation"""
        session = self.get_current_session()
        
        # Update performance tracking
        if session.value not in self.session_performance:
            self.session_performance[session.value] = {'total': 0, 'successful': 0}
        self.session_performance[session.value]['total'] += 1
        if success:
            self.session_performance[session.value]['successful'] += 1
        
        if strategy_type not in self.strategy_performance:
            self.strategy_performance[strategy_type] = {'total': 0, 'successful': 0}
        self.strategy_performance[strategy_type]['total'] += 1
        if success:
            self.strategy_performance[strategy_type]['successful'] += 1
        
        # Learn from outcome using base agent method
        decision = f"Timing strategy: {strategy_type} for {symbol} during {session.value}"
        outcome = f"Entry: {entry_time}, Exit: {exit_time}, P&L: ${profit_loss:.2f}"
        
        self.learn_from_outcome(decision, outcome, success, profit_loss)
        
        # Store specific timing outcome
        content = f"Timing outcome for {symbol}: {strategy_type} strategy resulted in {'success' if success else 'failure'} with P&L of ${profit_loss:.2f}"
        
        metadata = {
            'symbol': symbol,
            'strategy_type': strategy_type,
            'session': session.value,
            'success': success,
            'profit_loss': profit_loss,
            'actual_hold_minutes': int((exit_time - entry_time).total_seconds() / 60),
            'entry_hour': entry_time.hour,
            'exit_hour': exit_time.hour
        }
        
        self.store_memory(content, "timing_outcome", metadata)
        
        timing_logger.info(f"Recorded timing outcome: {symbol} {strategy_type} {'SUCCESS' if success else 'FAILURE'} ${profit_loss:.2f}")
    
    def analyze_volatility_window(self, symbol: str) -> Dict[str, float]:
        """Analyze current volatility conditions with memory enhancement"""
        current_session = self.get_current_session()
        now = datetime.now()
        
        if current_session == MarketSession.CLOSED:
            return {"volatility_score": 0.0, "volume_score": 0.0, "timing_score": 0.0}
        
        # Base volatility analysis
        volatility_score = 0.0
        volume_score = 0.0
        timing_score = 0.0
        
        if current_session == MarketSession.PRE_MARKET:
            if 4 <= now.hour < 6:
                volatility_score = 0.9
                volume_score = 0.3
                timing_score = 0.6
            elif 6 <= now.hour < 9:
                volatility_score = 0.7
                volume_score = 0.6
                timing_score = 0.8
        
        elif current_session == MarketSession.REGULAR:
            if 9.5 <= now.hour < 11:
                volatility_score = 0.95
                volume_score = 0.9
                timing_score = 0.9
            elif 11 <= now.hour < 15:
                volatility_score = 0.6
                volume_score = 0.7
                timing_score = 0.7
            else:
                volatility_score = 0.8
                volume_score = 0.8
                timing_score = 0.75
        
        elif current_session == MarketSession.AFTER_HOURS:
            volatility_score = 0.4
            volume_score = 0.2
            timing_score = 0.3
        
        # Enhance with memory-based adjustments
        session_accuracy = self._get_session_accuracy(current_session)
        if session_accuracy > 0:
            # Adjust timing score based on historical session performance
            timing_score *= (0.8 + (session_accuracy * 0.4))
        
        return {
            "volatility_score": volatility_score,
            "volume_score": volume_score,
            "timing_score": timing_score,
            "overall_score": (volatility_score + volume_score + timing_score) / 3,
            "session_accuracy": session_accuracy
        }
    
    async def get_session_analytics(self) -> Dict[str, any]:
        """Get comprehensive session analytics with memory insights"""
        current_session = self.get_current_session()
        now = datetime.now()
        
        base_analytics = {
            "current_session": current_session.value,
            "session_start": self._get_session_start(current_session),
            "session_end": self._get_session_end(current_session),
            "time_remaining": self._get_time_remaining_in_session(current_session),
            "next_session": self._get_next_session(current_session),
            "optimal_strategies": self._get_optimal_strategies_for_session(current_session),
            "volatility_forecast": self._forecast_volatility(current_session)
        }
        
        # Add memory-based performance insights
        base_analytics.update({
            "session_performance": self.session_performance.get(current_session.value, {}),
            "strategy_performance": self.strategy_performance,
            "total_timing_experiences": len(self.memory_cache),
            "agent_accuracy": self.performance_metrics.get('accuracy_rate', 0.0)
        })
        
        return base_analytics
    
    def _next_market_open(self) -> datetime:
        """Calculate next market open time"""
        now = datetime.now()
        next_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        
        if now.time() >= time(16, 0):
            next_open += timedelta(days=1)
        
        while next_open.weekday() > 4:
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
        """Get optimal trading strategies for current session with memory enhancement"""
        base_strategies = {
            MarketSession.PRE_MARKET: ["momentum", "gap_trading", "news_reaction"],
            MarketSession.REGULAR: ["momentum", "scalping", "swing_trading", "mean_reversion"],
            MarketSession.AFTER_HOURS: ["mean_reversion", "position_holding"],
            MarketSession.CLOSED: ["analysis", "planning", "research"]
        }
        
        strategies = base_strategies.get(session, ["analysis"])
        
        # Rank strategies by historical performance
        if session != MarketSession.CLOSED:
            strategy_scores = []
            for strategy in strategies:
                accuracy = self._get_strategy_accuracy(strategy)
                strategy_scores.append((strategy, accuracy))
            
            # Sort by accuracy, keeping original order for ties
            strategy_scores.sort(key=lambda x: x[1], reverse=True)
            strategies = [s[0] for s in strategy_scores]
        
        return strategies
    
    def _forecast_volatility(self, session: MarketSession) -> Dict[str, float]:
        """Forecast volatility for different time horizons with memory enhancement"""
        base_volatility = {
            MarketSession.PRE_MARKET: 0.7,
            MarketSession.REGULAR: 0.9,
            MarketSession.AFTER_HOURS: 0.4,
            MarketSession.CLOSED: 0.0
        }
        
        current_vol = base_volatility.get(session, 0.0)
        
        # Adjust based on recent session performance
        session_accuracy = self._get_session_accuracy(session)
        if session_accuracy > 0:
            # Higher accuracy might indicate more predictable (lower) volatility
            volatility_adjustment = (0.7 - session_accuracy) * 0.3
            current_vol = max(0.1, current_vol + volatility_adjustment)
        
        return {
            "current": current_vol,
            "15min": current_vol * 0.9,
            "1hour": current_vol * 0.8,
            "4hour": current_vol * 0.6,
            "daily": current_vol * 0.5,
            "confidence": session_accuracy
        }
    
    async def process(self):
        """Main processing loop for timing agent"""
        while self.is_active:
            try:
                current_session = self.get_current_session()
                
                # Update status
                self.update_status(f"Monitoring {current_session.value} session")
                
                # Analyze current market conditions
                volatility_analysis = self.analyze_volatility_window("MARKET")
                
                # Log insights
                if volatility_analysis["overall_score"] > 0.8:
                    timing_logger.info(f"High opportunity window detected: {volatility_analysis}")
                
                # Store market condition analysis
                self.store_memory(
                    content=f"Market condition analysis: {current_session.value} session with overall score {volatility_analysis['overall_score']:.2f}",
                    memory_type="market_condition",
                    metadata={
                        'session': current_session.value,
                        'volatility_score': volatility_analysis['volatility_score'],
                        'timing_score': volatility_analysis['timing_score'],
                        'overall_score': volatility_analysis['overall_score']
                    }
                )
                
                # Wait before next analysis
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error in timing agent process: {e}")
                await asyncio.sleep(60)

# Main execution
if __name__ == "__main__":
    async def main():
        timing_agent = MarketTimingAgent()
        await timing_agent.start()
        
        # Example usage
        signal = await timing_agent.analyze_optimal_entry("AAPL", "momentum")
        print(f"Timing Signal for AAPL:")
        print(f"  Session: {signal.session.value}")
        print(f"  Optimal Entry: {signal.optimal_entry}")
        print(f"  Optimal Exit: {signal.optimal_exit}")
        print(f"  Volatility Window: {signal.volatility_window}")
        print(f"  Confidence: {signal.confidence:.2%}")
        print(f"  Risk Level: {signal.risk_level}")
        print(f"  Expected Hold Time: {signal.expected_hold_time}")
        print(f"  Reasoning: {signal.reasoning}")
        
        # Session analytics
        analytics = await timing_agent.get_session_analytics()
        print(f"\nSession Analytics:")
        for key, value in analytics.items():
            print(f"  {key}: {value}")
        
        await timing_agent.stop()
    
    asyncio.run(main())
