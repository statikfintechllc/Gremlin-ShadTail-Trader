#!/usr/bin/env python3
"""
Gremlin ShadTail Trader - Agent Coordinator
Master coordinator for all trading agents with memory-based orchestration
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Import all agents
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from Gremlin_Trade_Core.Gremlin_Trader_Tools.Memory_Agent.base_memory_agent import BaseMemoryAgent
from Gremlin_Trader_Tools.Timing_Agent.market_timing import MarketTimingAgent
from Gremlin_Trader_Tools.Strategy_Agent.strategy_agent import StrategyAgent
from Gremlin_Trader_Tools.Rule_Set_Agent.rule_set_agent import RuleSetAgent
from Gremlin_Trader_Tools.Run_Time_Agent.runtime_agent import RuntimeAgent

class CoordinationMode(Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    AUTONOMOUS = "autonomous"

class TradingPhase(Enum):
    MARKET_ANALYSIS = "market_analysis"
    SIGNAL_GENERATION = "signal_generation"
    RULE_VALIDATION = "rule_validation"
    TIMING_OPTIMIZATION = "timing_optimization"
    EXECUTION_PLANNING = "execution_planning"
    MONITORING = "monitoring"

@dataclass
class TradingDecision:
    symbol: str
    action: str  # 'buy', 'sell', 'hold'
    confidence: float
    position_size: float
    entry_price: float
    stop_loss: float
    take_profit: float
    reasoning: str
    contributing_agents: List[str]
    risk_score: float
    timestamp: datetime

class AgentCoordinator(BaseMemoryAgent):
    """
    Master coordinator that orchestrates all trading agents with memory-based learning
    """
    
    def __init__(self):
        super().__init__("AgentCoordinator", "coordinator")
        
        # Initialize agents
        self.timing_agent = None
        self.strategy_agent = None
        self.rule_agent = None
        self.runtime_agent = None
        
        # Coordination parameters
        self.coordination_mode = CoordinationMode.BALANCED
        self.trading_phase = TradingPhase.MARKET_ANALYSIS
        self.consensus_threshold = 0.7
        self.max_position_risk = 0.05  # 5% of portfolio per position
        
        # Decision tracking
        self.pending_decisions: Dict[str, TradingDecision] = {}
        self.executed_decisions: Dict[str, TradingDecision] = {}
        self.agent_weights = {
            'timing': 0.25,
            'strategy': 0.35,
            'rules': 0.25,
            'runtime': 0.15
        }
        
        # Performance tracking
        self.coordination_performance = {
            'total_decisions': 0,
            'successful_decisions': 0,
            'failed_decisions': 0,
            'accuracy': 0.0,
            'total_pnl': 0.0
        }
        
        # Watchlist management
        self.active_watchlist = ["AAPL", "MSFT", "TSLA", "NVDA", "SPY", "QQQ"]
        self.symbol_priorities = {}
        
        self.logger.info("Agent Coordinator initialized")
    
    async def initialize_agents(self):
        """Initialize and start all trading agents"""
        try:
            self.logger.info("Initializing trading agents...")
            
            # Initialize Runtime Agent first
            self.runtime_agent = RuntimeAgent()
            await self.runtime_agent.start()
            
            # Initialize other agents
            self.timing_agent = MarketTimingAgent()
            self.strategy_agent = StrategyAgent()
            self.rule_agent = RuleSetAgent()
            
            # Register agents with runtime agent
            await self.runtime_agent.register_agent("timing_agent", self.timing_agent)
            await self.runtime_agent.register_agent("strategy_agent", self.strategy_agent)
            await self.runtime_agent.register_agent("rule_agent", self.rule_agent)
            
            # Start all agents
            await self.timing_agent.start()
            await self.strategy_agent.start()
            await self.rule_agent.start()
            
            # Start runtime management
            await self.runtime_agent.start_agent("timing_agent")
            await self.runtime_agent.start_agent("strategy_agent")
            await self.runtime_agent.start_agent("rule_agent")
            
            self.logger.info("All trading agents initialized and started")
            
        except Exception as e:
            self.logger.error(f"Error initializing agents: {e}")
            raise
    
    async def shutdown_agents(self):
        """Shutdown all trading agents"""
        try:
            self.logger.info("Shutting down trading agents...")
            
            agents = [
                ("timing_agent", self.timing_agent),
                ("strategy_agent", self.strategy_agent),
                ("rule_agent", self.rule_agent),
                ("runtime_agent", self.runtime_agent)
            ]
            
            for agent_name, agent in agents:
                if agent:
                    try:
                        await agent.stop()
                        self.logger.info(f"Stopped {agent_name}")
                    except Exception as e:
                        self.logger.error(f"Error stopping {agent_name}: {e}")
            
            self.logger.info("All agents shut down")
            
        except Exception as e:
            self.logger.error(f"Error shutting down agents: {e}")
    
    async def coordinate_trading_decision(self, symbol: str) -> Optional[TradingDecision]:
        """Coordinate trading decision for a symbol across all agents"""
        try:
            self.logger.info(f"Coordinating trading decision for {symbol}")
            
            # Phase 1: Market Analysis
            self.trading_phase = TradingPhase.MARKET_ANALYSIS
            market_conditions = await self.strategy_agent.analyze_market_conditions()
            
            # Phase 2: Signal Generation
            self.trading_phase = TradingPhase.SIGNAL_GENERATION
            strategy_signals = await self.strategy_agent.generate_signals([symbol])
            
            # Phase 3: Timing Analysis
            timing_analysis = await self.timing_agent.analyze_symbol(symbol)
            
            # Phase 4: Rule Validation
            self.trading_phase = TradingPhase.RULE_VALIDATION
            
            # Prepare market data for rule evaluation
            market_data = {
                'symbol': symbol,
                'price': 0.0,  # Would get from market data service
                'volume': 0,
                'rsi': 50,
                'ema_20': 0.0,
                'volatility': market_conditions.get('volatility', 0.2)
            }
            
            # Get latest strategy signal for this symbol
            strategy_signal = None
            for signal in strategy_signals:
                if signal.symbol == symbol:
                    strategy_signal = signal
                    market_data.update({
                        'price': signal.entry_price,
                        'rsi': signal.indicators.get('rsi', 50)
                    })
                    break
            
            # Evaluate rules
            rule_evaluations = await self.rule_agent.evaluate_rules(symbol, market_data)
            
            # Phase 5: Decision Synthesis
            decision = await self._synthesize_decision(
                symbol, strategy_signal, timing_analysis, rule_evaluations, market_conditions
            )
            
            if decision:
                # Store decision for tracking
                self.pending_decisions[symbol] = decision
                
                # Store coordination decision in memory
                await self._store_coordination_decision(decision)
                
                self.logger.info(f"Trading decision for {symbol}: {decision.action} with {decision.confidence:.2%} confidence")
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Error coordinating trading decision for {symbol}: {e}")
            return None
    
    async def _synthesize_decision(self, symbol: str, strategy_signal, timing_analysis, 
                                 rule_evaluations, market_conditions) -> Optional[TradingDecision]:
        """Synthesize inputs from all agents into a trading decision"""
        try:
            # Collect agent inputs
            agent_inputs = {
                'strategy': strategy_signal,
                'timing': timing_analysis,
                'rules': rule_evaluations,
                'market': market_conditions
            }
            
            # Calculate weighted confidence
            confidence_scores = {}
            contributing_agents = []
            reasoning_parts = []
            
            # Strategy Agent Input
            if strategy_signal:
                confidence_scores['strategy'] = strategy_signal.confidence
                contributing_agents.append('strategy')
                reasoning_parts.append(f"Strategy: {strategy_signal.strategy_type.value} ({strategy_signal.confidence:.1%})")
            
            # Timing Agent Input
            if timing_analysis:
                confidence_scores['timing'] = timing_analysis.confidence
                contributing_agents.append('timing')
                reasoning_parts.append(f"Timing: {timing_analysis.signal.value} ({timing_analysis.confidence:.1%})")
            
            # Rule Agent Input
            triggered_rules = [eval for eval in rule_evaluations if eval.triggered]
            if triggered_rules:
                rule_confidence = sum(eval.confidence for eval in triggered_rules) / len(triggered_rules)
                confidence_scores['rules'] = rule_confidence
                contributing_agents.append('rules')
                reasoning_parts.append(f"Rules: {len(triggered_rules)} triggered ({rule_confidence:.1%})")
            
            # Market Conditions
            market_confidence = self._assess_market_confidence(market_conditions)
            confidence_scores['market'] = market_confidence
            reasoning_parts.append(f"Market: {market_conditions.get('trend', 'unknown')} ({market_confidence:.1%})")
            
            # Calculate weighted overall confidence
            total_weight = sum(self.agent_weights[agent] for agent in confidence_scores.keys())
            if total_weight == 0:
                return None
            
            overall_confidence = sum(
                confidence_scores[agent] * self.agent_weights[agent]
                for agent in confidence_scores.keys()
            ) / total_weight
            
            # Check consensus threshold
            if overall_confidence < self.consensus_threshold:
                self.logger.info(f"Insufficient consensus for {symbol}: {overall_confidence:.2%} < {self.consensus_threshold:.2%}")
                return None
            
            # Determine action
            action = "hold"
            entry_price = 0.0
            stop_loss = 0.0
            take_profit = 0.0
            
            if strategy_signal:
                entry_price = strategy_signal.entry_price
                stop_loss = strategy_signal.stop_loss
                take_profit = strategy_signal.take_profit
                
                # Determine action based on strategy signal
                if strategy_signal.signal_strength.value in ['strong', 'very_strong']:
                    action = "buy"  # Simplified - would consider direction
                elif strategy_signal.signal_strength.value == 'moderate':
                    action = "buy" if overall_confidence > 0.8 else "hold"
            
            # Adjust based on timing
            if timing_analysis and action == "buy":
                if timing_analysis.signal.value in ['sell', 'strong_sell']:
                    action = "hold"  # Timing conflicts with strategy
                elif timing_analysis.signal.value in ['buy', 'strong_buy']:
                    # Timing confirms strategy
                    overall_confidence *= 1.1
            
            # Final rule validation
            entry_rules_passed = any(
                eval.triggered and eval.rule_id.startswith('entry') 
                for eval in rule_evaluations
            )
            
            if action == "buy" and not entry_rules_passed:
                action = "hold"  # Rules prevent entry
                reasoning_parts.append("Entry blocked by rules")
            
            # Calculate position size
            position_size = self._calculate_position_size(overall_confidence, stop_loss, entry_price)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(market_conditions, overall_confidence, position_size)
            
            # Adjust for coordination mode
            action, overall_confidence, position_size = self._adjust_for_coordination_mode(
                action, overall_confidence, position_size, risk_score
            )
            
            # Create decision
            decision = TradingDecision(
                symbol=symbol,
                action=action,
                confidence=min(0.95, overall_confidence),
                position_size=position_size,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reasoning=" | ".join(reasoning_parts),
                contributing_agents=contributing_agents,
                risk_score=risk_score,
                timestamp=datetime.now(timezone.utc)
            )
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Error synthesizing decision for {symbol}: {e}")
            return None
    
    def _assess_market_confidence(self, market_conditions: Dict) -> float:
        """Assess market confidence based on conditions"""
        try:
            base_confidence = 0.5
            
            # Volatility factor
            volatility = market_conditions.get('volatility', 0.2)
            if 0.15 <= volatility <= 0.25:
                base_confidence += 0.2  # Optimal volatility
            elif volatility > 0.35:
                base_confidence -= 0.3  # High volatility reduces confidence
            
            # Trend factor
            trend = market_conditions.get('trend', 'unknown')
            if trend == 'bullish':
                base_confidence += 0.2
            elif trend == 'bearish':
                base_confidence -= 0.1
            
            # VIX factor
            vix = market_conditions.get('vix', 20)
            if vix < 20:
                base_confidence += 0.1
            elif vix > 30:
                base_confidence -= 0.2
            
            return max(0.1, min(0.9, base_confidence))
            
        except Exception:
            return 0.5
    
    def _calculate_position_size(self, confidence: float, stop_loss: float, entry_price: float) -> float:
        """Calculate position size based on confidence and risk"""
        try:
            if entry_price == 0 or stop_loss == 0:
                return 0.01  # Minimum size
            
            # Base position size on confidence
            base_size = 0.02 + (confidence * 0.03)  # 2-5% based on confidence
            
            # Adjust for stop distance
            stop_distance = abs(entry_price - stop_loss) / entry_price
            if stop_distance > 0:
                # Smaller size for wider stops
                size_adjustment = min(1.0, 0.02 / stop_distance)
                base_size *= size_adjustment
            
            # Apply maximum position risk
            final_size = min(base_size, self.max_position_risk)
            
            return round(final_size, 4)
            
        except Exception:
            return 0.01
    
    def _calculate_risk_score(self, market_conditions: Dict, confidence: float, position_size: float) -> float:
        """Calculate overall risk score"""
        try:
            risk_score = 0.0
            
            # Volatility risk
            volatility = market_conditions.get('volatility', 0.2)
            risk_score += min(0.4, volatility * 2)
            
            # Confidence risk (inverse)
            risk_score += (1 - confidence) * 0.3
            
            # Position size risk
            risk_score += position_size * 5  # Convert percentage to risk factor
            
            # Market condition risk
            vix = market_conditions.get('vix', 20)
            if vix > 25:
                risk_score += 0.2
            
            return min(1.0, risk_score)
            
        except Exception:
            return 0.5
    
    def _adjust_for_coordination_mode(self, action: str, confidence: float, 
                                    position_size: float, risk_score: float) -> tuple:
        """Adjust decision based on coordination mode"""
        try:
            if self.coordination_mode == CoordinationMode.CONSERVATIVE:
                # Increase thresholds, reduce sizes
                if confidence < 0.8:
                    action = "hold"
                position_size *= 0.7
                confidence *= 0.9
                
            elif self.coordination_mode == CoordinationMode.AGGRESSIVE:
                # Lower thresholds, increase sizes
                if action == "hold" and confidence > 0.6:
                    action = "buy"
                position_size *= 1.3
                confidence *= 1.05
                
            elif self.coordination_mode == CoordinationMode.AUTONOMOUS:
                # Let AI make decisions with minimal constraints
                if risk_score > 0.7:
                    position_size *= 0.8
                
            # Balanced mode requires no adjustments
            
            return action, min(0.95, confidence), min(self.max_position_risk, position_size)
            
        except Exception:
            return action, confidence, position_size
    
    async def _store_coordination_decision(self, decision: TradingDecision):
        """Store coordination decision in memory"""
        try:
            content = f"Coordination decision: {decision.action} {decision.symbol} at ${decision.entry_price:.2f} with {decision.confidence:.2%} confidence"
            
            metadata = {
                'symbol': decision.symbol,
                'action': decision.action,
                'confidence': decision.confidence,
                'position_size': decision.position_size,
                'entry_price': decision.entry_price,
                'risk_score': decision.risk_score,
                'contributing_agents': decision.contributing_agents,
                'coordination_mode': self.coordination_mode.value,
                'trading_phase': self.trading_phase.value
            }
            
            self.store_memory(content, "coordination_decision", metadata)
            
        except Exception as e:
            self.logger.error(f"Error storing coordination decision: {e}")
    
    async def execute_coordinated_trading(self):
        """Execute coordinated trading across all symbols"""
        try:
            self.logger.info("Starting coordinated trading cycle")
            
            decisions = []
            
            # Process each symbol in watchlist
            for symbol in self.active_watchlist:
                try:
                    decision = await self.coordinate_trading_decision(symbol)
                    if decision and decision.action != "hold":
                        decisions.append(decision)
                        
                except Exception as e:
                    self.logger.error(f"Error processing {symbol}: {e}")
            
            # Sort decisions by confidence and risk
            decisions.sort(key=lambda d: d.confidence - d.risk_score, reverse=True)
            
            # Execute top decisions (limit to avoid overexposure)
            max_positions = 3 if self.coordination_mode == CoordinationMode.CONSERVATIVE else 5
            
            for i, decision in enumerate(decisions[:max_positions]):
                self.logger.info(f"Decision {i+1}: {decision.action} {decision.symbol} - Confidence: {decision.confidence:.2%}, Risk: {decision.risk_score:.2f}")
                
                # Here would integrate with actual trading execution
                # For now, just track the decision
                self.executed_decisions[decision.symbol] = decision
            
            self.logger.info(f"Coordinated trading cycle completed: {len(decisions)} decisions, {min(len(decisions), max_positions)} executed")
            
        except Exception as e:
            self.logger.error(f"Error in coordinated trading: {e}")
    
    async def record_trading_outcome(self, symbol: str, success: bool, profit_loss: float):
        """Record outcome of a coordinated trading decision"""
        try:
            if symbol not in self.executed_decisions:
                return
            
            decision = self.executed_decisions[symbol]
            
            # Update coordination performance
            self.coordination_performance['total_decisions'] += 1
            if success:
                self.coordination_performance['successful_decisions'] += 1
            else:
                self.coordination_performance['failed_decisions'] += 1
            
            self.coordination_performance['accuracy'] = (
                self.coordination_performance['successful_decisions'] / 
                self.coordination_performance['total_decisions']
            )
            self.coordination_performance['total_pnl'] += profit_loss
            
            # Learn from outcome
            outcome_description = f"Coordinated trade: {decision.action} {symbol} at ${decision.entry_price:.2f} resulted in {'profit' if success else 'loss'} of ${profit_loss:.2f}"
            
            self.learn_from_outcome(
                decision=f"Coordination decision: {decision.action} {symbol}",
                outcome=outcome_description,
                success=success,
                profit_loss=profit_loss
            )
            
            # Update individual agent outcomes
            for agent_name in decision.contributing_agents:
                if agent_name == 'strategy' and self.strategy_agent:
                    await self.strategy_agent.record_strategy_outcome(
                        symbol, decision.action, success, profit_loss
                    )
                elif agent_name == 'timing' and self.timing_agent:
                    await self.timing_agent.record_timing_outcome(
                        symbol, decision.action, datetime.now(), datetime.now(), success, profit_loss
                    )
                elif agent_name == 'rules' and self.rule_agent:
                    # Find triggered rules for this symbol
                    for rule_id in [f"entry_{symbol}", f"exit_{symbol}"]:  # Simplified
                        await self.rule_agent.record_rule_outcome(rule_id, symbol, success, profit_loss)
            
            # Store coordination outcome
            content = f"Coordination outcome: {symbol} {'SUCCESS' if success else 'FAILURE'} with P&L ${profit_loss:.2f}"
            
            metadata = {
                'symbol': symbol,
                'success': success,
                'profit_loss': profit_loss,
                'original_confidence': decision.confidence,
                'original_risk_score': decision.risk_score,
                'contributing_agents': decision.contributing_agents,
                'coordination_accuracy': self.coordination_performance['accuracy']
            }
            
            self.store_memory(content, "coordination_outcome", metadata)
            
            # Remove from executed decisions
            del self.executed_decisions[symbol]
            
            self.logger.info(f"Recorded coordination outcome for {symbol}: {'SUCCESS' if success else 'FAILURE'} ${profit_loss:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error recording trading outcome for {symbol}: {e}")
    
    async def get_coordination_overview(self) -> Dict:
        """Get comprehensive coordination overview"""
        try:
            # Get overviews from all agents
            timing_overview = await self.timing_agent.get_market_timing_overview() if self.timing_agent else {}
            strategy_overview = await self.strategy_agent.get_strategy_overview() if self.strategy_agent else {}
            rule_overview = await self.rule_agent.get_rule_overview() if self.rule_agent else {}
            runtime_overview = await self.runtime_agent.get_runtime_overview() if self.runtime_agent else {}
            
            return {
                'coordinator_status': self.get_agent_state(),
                'coordination_mode': self.coordination_mode.value,
                'trading_phase': self.trading_phase.value,
                'performance': self.coordination_performance,
                'active_watchlist': self.active_watchlist,
                'pending_decisions': len(self.pending_decisions),
                'executed_decisions': len(self.executed_decisions),
                'agent_weights': self.agent_weights,
                'consensus_threshold': self.consensus_threshold,
                'agent_overviews': {
                    'timing': timing_overview,
                    'strategy': strategy_overview,
                    'rules': rule_overview,
                    'runtime': runtime_overview
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting coordination overview: {e}")
            return {}
    
    async def update_coordination_mode(self, new_mode: CoordinationMode):
        """Update coordination mode"""
        try:
            old_mode = self.coordination_mode
            self.coordination_mode = new_mode
            
            # Adjust parameters based on mode
            if new_mode == CoordinationMode.CONSERVATIVE:
                self.consensus_threshold = 0.8
                self.max_position_risk = 0.03
            elif new_mode == CoordinationMode.AGGRESSIVE:
                self.consensus_threshold = 0.6
                self.max_position_risk = 0.07
            elif new_mode == CoordinationMode.AUTONOMOUS:
                self.consensus_threshold = 0.5
                self.max_position_risk = 0.1
            else:  # BALANCED
                self.consensus_threshold = 0.7
                self.max_position_risk = 0.05
            
            content = f"Coordination mode changed from {old_mode.value} to {new_mode.value}"
            metadata = {
                'old_mode': old_mode.value,
                'new_mode': new_mode.value,
                'new_consensus_threshold': self.consensus_threshold,
                'new_max_position_risk': self.max_position_risk
            }
            
            self.store_memory(content, "mode_change", metadata)
            
            self.logger.info(f"Coordination mode updated to {new_mode.value}")
            
        except Exception as e:
            self.logger.error(f"Error updating coordination mode: {e}")
    
    async def process(self):
        """Main coordination processing loop"""
        while self.is_active:
            try:
                # Update status
                active_decisions = len(self.executed_decisions)
                accuracy = self.coordination_performance.get('accuracy', 0.0)
                
                self.update_status(
                    f"Coordinating {len(self.active_watchlist)} symbols, "
                    f"{active_decisions} active decisions, "
                    f"{accuracy:.1%} accuracy"
                )
                
                # Execute coordinated trading
                await self.execute_coordinated_trading()
                
                # Clean up old decisions (older than 24 hours)
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
                expired_decisions = [
                    symbol for symbol, decision in self.executed_decisions.items()
                    if decision.timestamp < cutoff_time
                ]
                
                for symbol in expired_decisions:
                    self.logger.info(f"Cleaning up expired decision for {symbol}")
                    del self.executed_decisions[symbol]
                
                # Wait before next cycle
                await asyncio.sleep(1800)  # 30 minutes
                
            except Exception as e:
                self.logger.error(f"Error in coordination main loop: {e}")
                await asyncio.sleep(300)  # 5 minutes on error

# Example usage
if __name__ == "__main__":
    async def main():
        coordinator = AgentCoordinator()
        
        try:
            await coordinator.start()
            await coordinator.initialize_agents()
            
            # Test coordination
            decision = await coordinator.coordinate_trading_decision("AAPL")
            if decision:
                print(f"Coordination Decision for AAPL:")
                print(f"  Action: {decision.action}")
                print(f"  Confidence: {decision.confidence:.2%}")
                print(f"  Position Size: {decision.position_size:.3f}")
                print(f"  Risk Score: {decision.risk_score:.2f}")
                print(f"  Contributing Agents: {decision.contributing_agents}")
                print(f"  Reasoning: {decision.reasoning}")
            
            # Get overview
            overview = await coordinator.get_coordination_overview()
            print(f"\nCoordination Overview:")
            print(f"  Mode: {overview.get('coordination_mode')}")
            print(f"  Performance: {overview.get('performance')}")
            print(f"  Active Watchlist: {len(overview.get('active_watchlist', []))}")
            
        finally:
            await coordinator.shutdown_agents()
            await coordinator.stop()
    
    asyncio.run(main())
