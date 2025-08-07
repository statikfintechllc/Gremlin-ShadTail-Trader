#!/usr/bin/env python3
"""
Gremlin ShadTail Trader - Rule Set Agent
Advanced rule-based trading system with memory-based learning and adaptive rules
"""

# Import ALL dependencies through globals.py (required)
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from Gremlin_Trade_Core.globals import (
    # Core imports that may be needed
    logging, datetime, asyncio, json, os, sys, Path,
    # Configuration and utilities
    setup_agent_logging, CFG, MEM, LOGS_DIR
)

# Use centralized logging
logger = setup_agent_logging(Path(__file__).stem)


import asyncio
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

# Import base memory agent
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from Gremlin_Trade_Core.Gremlin_Trader_Tools.Memory_Agent.base_memory_agent import BaseMemoryAgent

class RuleType(Enum):
    ENTRY = "entry"
    EXIT = "exit"
    RISK_MANAGEMENT = "risk_management"
    POSITION_SIZING = "position_sizing"
    MARKET_CONDITION = "market_condition"

class RuleOperator(Enum):
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="
    BETWEEN = "between"
    NOT_BETWEEN = "not_between"
    CROSSES_ABOVE = "crosses_above"
    CROSSES_BELOW = "crosses_below"

class RuleLogic(Enum):
    AND = "and"
    OR = "or"
    NOT = "not"

@dataclass
class TradingRule:
    rule_id: str
    rule_type: RuleType
    name: str
    description: str
    condition: str  # Human readable condition
    parameters: Dict[str, Any]
    operator: RuleOperator
    threshold: float
    priority: int = 1
    enabled: bool = True
    success_count: int = 0
    failure_count: int = 0
    accuracy: float = 0.0
    last_triggered: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def get_success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0
    
    def update_performance(self, success: bool):
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        self.accuracy = self.get_success_rate()

@dataclass
class RuleSet:
    name: str
    rules: List[TradingRule]
    logic: RuleLogic
    enabled: bool = True
    success_count: int = 0
    failure_count: int = 0
    
    def get_success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0

@dataclass
class RuleEvaluation:
    rule_id: str
    symbol: str
    triggered: bool
    value: float
    threshold: float
    condition_met: bool
    confidence: float
    reasoning: str
    timestamp: datetime

class RuleSetAgent(BaseMemoryAgent):
    """
    Advanced rule-based trading agent with memory-based learning and adaptive rules
    """
    
    def __init__(self):
        super().__init__("RuleSetAgent", "rules")
        
        # Rule storage
        self.rules: Dict[str, TradingRule] = {}
        self.rule_sets: Dict[str, RuleSet] = {}
        
        # Rule performance tracking
        self.rule_performance_history = {}
        self.adaptive_learning = True
        self.min_rule_confidence = 0.6
        
        # Rule evaluation cache
        self.evaluation_cache = {}
        self.cache_expiry = 300  # 5 minutes
        
        # Initialize default rules
        self._initialize_default_rules()
        
        # Load learned rules from memory
        self._load_rules_from_memory()
        
        self.logger.info("Rule Set Agent initialized with memory integration")
    
    def _initialize_default_rules(self):
        """Initialize default trading rules"""
        
        # Entry Rules
        momentum_entry = TradingRule(
            rule_id="momentum_entry_1",
            rule_type=RuleType.ENTRY,
            name="Momentum Breakout Entry",
            description="Enter long when price breaks above EMA with volume confirmation",
            condition="price > ema_20 AND volume > avg_volume * 1.5 AND rsi > 50",
            parameters={"ema_period": 20, "volume_multiplier": 1.5, "rsi_threshold": 50},
            operator=RuleOperator.GREATER_THAN,
            threshold=0.0,
            priority=1
        )
        
        oversold_entry = TradingRule(
            rule_id="oversold_entry_1",
            rule_type=RuleType.ENTRY,
            name="Oversold Bounce Entry",
            description="Enter long when RSI is oversold and price near support",
            condition="rsi < 30 AND price > support_level * 0.98",
            parameters={"rsi_threshold": 30, "support_buffer": 0.02},
            operator=RuleOperator.LESS_THAN,
            threshold=30.0,
            priority=2
        )
        
        breakout_entry = TradingRule(
            rule_id="breakout_entry_1",
            rule_type=RuleType.ENTRY,
            name="Volume Breakout Entry",
            description="Enter on high volume breakout above resistance",
            condition="price > resistance_level AND volume > avg_volume * 2.0",
            parameters={"volume_multiplier": 2.0, "resistance_buffer": 0.01},
            operator=RuleOperator.GREATER_THAN,
            threshold=0.0,
            priority=1
        )
        
        # Exit Rules
        profit_exit = TradingRule(
            rule_id="profit_exit_1",
            rule_type=RuleType.EXIT,
            name="Profit Target Exit",
            description="Exit when profit target is reached",
            condition="current_profit >= profit_target",
            parameters={"profit_target_pct": 0.05},
            operator=RuleOperator.GREATER_EQUAL,
            threshold=0.05,
            priority=1
        )
        
        stop_loss_exit = TradingRule(
            rule_id="stop_loss_exit_1",
            rule_type=RuleType.EXIT,
            name="Stop Loss Exit",
            description="Exit when stop loss is hit",
            condition="current_loss >= stop_loss_limit",
            parameters={"stop_loss_pct": 0.03},
            operator=RuleOperator.GREATER_EQUAL,
            threshold=0.03,
            priority=1
        )
        
        trailing_stop_exit = TradingRule(
            rule_id="trailing_stop_exit_1",
            rule_type=RuleType.EXIT,
            name="Trailing Stop Exit",
            description="Exit on trailing stop activation",
            condition="price < highest_price * (1 - trailing_stop_pct)",
            parameters={"trailing_stop_pct": 0.02},
            operator=RuleOperator.LESS_THAN,
            threshold=0.02,
            priority=2
        )
        
        # Risk Management Rules
        position_size_rule = TradingRule(
            rule_id="position_size_1",
            rule_type=RuleType.POSITION_SIZING,
            name="Risk-Based Position Sizing",
            description="Calculate position size based on risk per trade",
            condition="position_size = risk_per_trade / stop_distance",
            parameters={"risk_per_trade": 0.02, "max_position_size": 0.1},
            operator=RuleOperator.LESS_EQUAL,
            threshold=0.1,
            priority=1
        )
        
        max_positions_rule = TradingRule(
            rule_id="max_positions_1",
            rule_type=RuleType.RISK_MANAGEMENT,
            name="Maximum Positions Limit",
            description="Limit total number of open positions",
            condition="open_positions < max_positions",
            parameters={"max_positions": 5},
            operator=RuleOperator.LESS_THAN,
            threshold=5.0,
            priority=1
        )
        
        correlation_rule = TradingRule(
            rule_id="correlation_1",
            rule_type=RuleType.RISK_MANAGEMENT,
            name="Correlation Risk Management",
            description="Avoid highly correlated positions",
            condition="position_correlation < max_correlation",
            parameters={"max_correlation": 0.7},
            operator=RuleOperator.LESS_THAN,
            threshold=0.7,
            priority=2
        )
        
        # Market Condition Rules
        volatility_rule = TradingRule(
            rule_id="volatility_1",
            rule_type=RuleType.MARKET_CONDITION,
            name="High Volatility Filter",
            description="Adjust strategy during high volatility",
            condition="vix < high_volatility_threshold",
            parameters={"high_volatility_threshold": 30},
            operator=RuleOperator.LESS_THAN,
            threshold=30.0,
            priority=1
        )
        
        trend_rule = TradingRule(
            rule_id="trend_1",
            rule_type=RuleType.MARKET_CONDITION,
            name="Market Trend Filter",
            description="Only trade in direction of major trend",
            condition="sma_20 > sma_50 AND sma_50 > sma_200",
            parameters={"trend_confirmation_periods": [20, 50, 200]},
            operator=RuleOperator.GREATER_THAN,
            threshold=0.0,
            priority=1
        )
        
        # Add rules to storage
        for rule in [momentum_entry, oversold_entry, breakout_entry, profit_exit, 
                    stop_loss_exit, trailing_stop_exit, position_size_rule, 
                    max_positions_rule, correlation_rule, volatility_rule, trend_rule]:
            self.rules[rule.rule_id] = rule
        
        # Create rule sets
        entry_rules = RuleSet(
            name="Entry Rules",
            rules=[momentum_entry, oversold_entry, breakout_entry],
            logic=RuleLogic.OR
        )
        
        exit_rules = RuleSet(
            name="Exit Rules",
            rules=[profit_exit, stop_loss_exit, trailing_stop_exit],
            logic=RuleLogic.OR
        )
        
        risk_rules = RuleSet(
            name="Risk Management Rules",
            rules=[position_size_rule, max_positions_rule, correlation_rule],
            logic=RuleLogic.AND
        )
        
        market_rules = RuleSet(
            name="Market Condition Rules",
            rules=[volatility_rule, trend_rule],
            logic=RuleLogic.AND
        )
        
        self.rule_sets = {
            "entry": entry_rules,
            "exit": exit_rules,
            "risk": risk_rules,
            "market": market_rules
        }
    
    def _load_rules_from_memory(self):
        """Load learned rules and performance from memory"""
        try:
            # Retrieve rule performance memories
            rule_memories = self.retrieve_memories(
                query="rule performance triggered success failure",
                memory_type="rule_performance",
                limit=100
            )
            
            # Update rule performance from memories
            for memory in rule_memories:
                metadata = memory.get('metadata', {})
                rule_id = metadata.get('rule_id')
                
                if rule_id and rule_id in self.rules:
                    rule = self.rules[rule_id]
                    rule.success_count = metadata.get('success_count', 0)
                    rule.failure_count = metadata.get('failure_count', 0)
                    rule.accuracy = metadata.get('accuracy', 0.0)
                    
                    if metadata.get('last_triggered'):
                        rule.last_triggered = datetime.fromisoformat(metadata['last_triggered'])
            
            # Retrieve adaptive rules
            adaptive_memories = self.retrieve_memories(
                query="adaptive rule learned generated",
                memory_type="adaptive_rule",
                limit=50
            )
            
            # Load adaptive rules
            for memory in adaptive_memories:
                metadata = memory.get('metadata', {})
                try:
                    rule_data = json.loads(memory['content'])
                    if self._validate_rule_data(rule_data):
                        adaptive_rule = self._create_rule_from_data(rule_data)
                        self.rules[adaptive_rule.rule_id] = adaptive_rule
                        self.logger.info(f"Loaded adaptive rule: {adaptive_rule.name}")
                except Exception as e:
                    self.logger.error(f"Error loading adaptive rule: {e}")
            
            self.logger.info(f"Loaded rules and performance from {len(rule_memories)} memories")
            
        except Exception as e:
            self.logger.error(f"Error loading rules from memory: {e}")
    
    def _validate_rule_data(self, rule_data: Dict) -> bool:
        """Validate rule data structure"""
        required_fields = ['rule_id', 'rule_type', 'name', 'condition', 'operator', 'threshold']
        return all(field in rule_data for field in required_fields)
    
    def _create_rule_from_data(self, rule_data: Dict) -> TradingRule:
        """Create TradingRule from data dictionary"""
        return TradingRule(
            rule_id=rule_data['rule_id'],
            rule_type=RuleType(rule_data['rule_type']),
            name=rule_data['name'],
            description=rule_data.get('description', ''),
            condition=rule_data['condition'],
            parameters=rule_data.get('parameters', {}),
            operator=RuleOperator(rule_data['operator']),
            threshold=rule_data['threshold'],
            priority=rule_data.get('priority', 1),
            enabled=rule_data.get('enabled', True),
            success_count=rule_data.get('success_count', 0),
            failure_count=rule_data.get('failure_count', 0),
            accuracy=rule_data.get('accuracy', 0.0)
        )
    
    async def evaluate_rules(self, symbol: str, market_data: Dict, rule_type: RuleType = None) -> List[RuleEvaluation]:
        """Evaluate rules for given symbol and market data"""
        try:
            evaluations = []
            
            # Filter rules by type if specified
            rules_to_evaluate = [
                rule for rule in self.rules.values()
                if rule.enabled and (rule_type is None or rule.rule_type == rule_type)
            ]
            
            for rule in rules_to_evaluate:
                try:
                    evaluation = await self._evaluate_single_rule(rule, symbol, market_data)
                    if evaluation:
                        evaluations.append(evaluation)
                        
                        # Store evaluation in memory if rule triggered
                        if evaluation.triggered:
                            await self._store_rule_evaluation(evaluation)
                        
                except Exception as e:
                    self.logger.error(f"Error evaluating rule {rule.rule_id}: {e}")
            
            return evaluations
            
        except Exception as e:
            self.logger.error(f"Error evaluating rules for {symbol}: {e}")
            return []
    
    async def _evaluate_single_rule(self, rule: TradingRule, symbol: str, market_data: Dict) -> Optional[RuleEvaluation]:
        """Evaluate a single trading rule"""
        try:
            # Extract values from market data based on rule condition
            value = self._extract_rule_value(rule, market_data)
            
            if value is None:
                return None
            
            # Evaluate condition
            condition_met = self._evaluate_condition(rule, value, market_data)
            triggered = condition_met and self._should_trigger_rule(rule, symbol)
            
            # Calculate confidence based on rule performance and market conditions
            confidence = self._calculate_rule_confidence(rule, market_data)
            
            # Generate reasoning
            reasoning = self._generate_rule_reasoning(rule, value, condition_met, confidence)
            
            evaluation = RuleEvaluation(
                rule_id=rule.rule_id,
                symbol=symbol,
                triggered=triggered,
                value=value,
                threshold=rule.threshold,
                condition_met=condition_met,
                confidence=confidence,
                reasoning=reasoning,
                timestamp=datetime.now(timezone.utc)
            )
            
            if triggered:
                rule.last_triggered = evaluation.timestamp
                self.logger.info(f"Rule triggered: {rule.name} for {symbol} - {reasoning}")
            
            return evaluation
            
        except Exception as e:
            self.logger.error(f"Error evaluating rule {rule.rule_id}: {e}")
            return None
    
    def _extract_rule_value(self, rule: TradingRule, market_data: Dict) -> Optional[float]:
        """Extract the relevant value from market data for rule evaluation"""
        try:
            # Map common rule parameters to market data fields
            value_map = {
                'price': market_data.get('price', 0),
                'volume': market_data.get('volume', 0),
                'rsi': market_data.get('rsi', 50),
                'ema_20': market_data.get('ema_20', market_data.get('price', 0)),
                'sma_20': market_data.get('sma_20', market_data.get('price', 0)),
                'sma_50': market_data.get('sma_50', market_data.get('price', 0)),
                'sma_200': market_data.get('sma_200', market_data.get('price', 0)),
                'vwap': market_data.get('vwap', market_data.get('price', 0)),
                'atr': market_data.get('atr', 0.02),
                'vix': market_data.get('vix', 20),
                'avg_volume': market_data.get('avg_volume', market_data.get('volume', 0)),
                'support_level': market_data.get('support', market_data.get('price', 0) * 0.95),
                'resistance_level': market_data.get('resistance', market_data.get('price', 0) * 1.05)
            }
            
            # Parse condition to extract primary value
            condition = rule.condition.lower()
            
            for key, value in value_map.items():
                if key in condition:
                    return float(value) if value is not None else 0.0
            
            # Default to threshold for comparison
            return rule.threshold
            
        except Exception as e:
            self.logger.error(f"Error extracting value for rule {rule.rule_id}: {e}")
            return None
    
    def _evaluate_condition(self, rule: TradingRule, value: float, market_data: Dict) -> bool:
        """Evaluate the rule condition"""
        try:
            threshold = rule.threshold
            
            if rule.operator == RuleOperator.GREATER_THAN:
                return value > threshold
            elif rule.operator == RuleOperator.LESS_THAN:
                return value < threshold
            elif rule.operator == RuleOperator.GREATER_EQUAL:
                return value >= threshold
            elif rule.operator == RuleOperator.LESS_EQUAL:
                return value <= threshold
            elif rule.operator == RuleOperator.EQUAL:
                return abs(value - threshold) < 0.001
            elif rule.operator == RuleOperator.NOT_EQUAL:
                return abs(value - threshold) >= 0.001
            elif rule.operator == RuleOperator.BETWEEN:
                # Expecting threshold to be a range [min, max]
                if isinstance(rule.parameters.get('range'), list):
                    range_vals = rule.parameters['range']
                    return range_vals[0] <= value <= range_vals[1]
                return False
            elif rule.operator == RuleOperator.CROSSES_ABOVE:
                # Need historical data for cross detection
                prev_value = market_data.get('prev_value', value)
                return prev_value <= threshold < value
            elif rule.operator == RuleOperator.CROSSES_BELOW:
                # Need historical data for cross detection
                prev_value = market_data.get('prev_value', value)
                return prev_value >= threshold > value
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error evaluating condition for rule {rule.rule_id}: {e}")
            return False
    
    def _should_trigger_rule(self, rule: TradingRule, symbol: str) -> bool:
        """Determine if rule should trigger based on additional criteria"""
        try:
            # Check minimum confidence threshold
            if rule.accuracy < self.min_rule_confidence and rule.success_count + rule.failure_count > 10:
                return False
            
            # Check if rule was recently triggered (avoid spam)
            if rule.last_triggered:
                time_since_trigger = datetime.now(timezone.utc) - rule.last_triggered
                if time_since_trigger < timedelta(minutes=5):
                    return False
            
            # Additional symbol-specific checks could go here
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking rule trigger for {rule.rule_id}: {e}")
            return False
    
    def _calculate_rule_confidence(self, rule: TradingRule, market_data: Dict) -> float:
        """Calculate confidence level for rule trigger"""
        try:
            base_confidence = 0.5
            
            # Historical performance contribution
            if rule.success_count + rule.failure_count > 0:
                performance_factor = rule.accuracy
                base_confidence += (performance_factor - 0.5) * 0.4
            
            # Market condition factors
            volatility = market_data.get('volatility', 0.2)
            volume_ratio = market_data.get('volume', 0) / max(market_data.get('avg_volume', 1), 1)
            
            # Higher volume increases confidence
            volume_factor = min(0.1, (volume_ratio - 1) * 0.05)
            base_confidence += volume_factor
            
            # Moderate volatility is preferred
            if 0.15 <= volatility <= 0.25:
                base_confidence += 0.1
            elif volatility > 0.35:
                base_confidence -= 0.2
            
            # Priority factor
            priority_factor = (rule.priority / 5) * 0.1
            base_confidence += priority_factor
            
            return max(0.1, min(0.95, base_confidence))
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence for rule {rule.rule_id}: {e}")
            return 0.5
    
    def _generate_rule_reasoning(self, rule: TradingRule, value: float, condition_met: bool, confidence: float) -> str:
        """Generate human-readable reasoning for rule evaluation"""
        try:
            status = "TRIGGERED" if condition_met else "NOT MET"
            accuracy_str = f"{rule.accuracy:.1%}" if rule.success_count + rule.failure_count > 0 else "NEW"
            
            reasoning = (
                f"{rule.name}: {status} | "
                f"Value: {value:.3f} vs Threshold: {rule.threshold:.3f} | "
                f"Confidence: {confidence:.1%} | "
                f"Historical Accuracy: {accuracy_str}"
            )
            
            return reasoning
            
        except Exception as e:
            self.logger.error(f"Error generating reasoning for rule {rule.rule_id}: {e}")
            return f"Rule {rule.rule_id} evaluation"
    
    async def _store_rule_evaluation(self, evaluation: RuleEvaluation):
        """Store rule evaluation in memory"""
        try:
            content = f"Rule evaluation: {evaluation.rule_id} for {evaluation.symbol} - {evaluation.reasoning}"
            
            metadata = {
                'rule_id': evaluation.rule_id,
                'symbol': evaluation.symbol,
                'triggered': evaluation.triggered,
                'value': evaluation.value,
                'threshold': evaluation.threshold,
                'condition_met': evaluation.condition_met,
                'confidence': evaluation.confidence
            }
            
            self.store_memory(content, "rule_evaluation", metadata)
            
        except Exception as e:
            self.logger.error(f"Error storing rule evaluation: {e}")
    
    async def learn_adaptive_rule(self, market_patterns: List[Dict], outcomes: List[bool]) -> Optional[TradingRule]:
        """Learn new rules from market patterns and outcomes"""
        try:
            if not self.adaptive_learning or len(market_patterns) < 10:
                return None
            
            # Analyze patterns to find correlations with successful outcomes
            successful_patterns = [pattern for pattern, outcome in zip(market_patterns, outcomes) if outcome]
            
            if len(successful_patterns) < 5:
                return None
            
            # Find common characteristics in successful patterns
            common_features = self._analyze_pattern_features(successful_patterns)
            
            if not common_features:
                return None
            
            # Generate new rule based on patterns
            new_rule = self._generate_adaptive_rule(common_features)
            
            if new_rule:
                self.rules[new_rule.rule_id] = new_rule
                
                # Store in memory
                rule_data = {
                    'rule_id': new_rule.rule_id,
                    'rule_type': new_rule.rule_type.value,
                    'name': new_rule.name,
                    'description': new_rule.description,
                    'condition': new_rule.condition,
                    'parameters': new_rule.parameters,
                    'operator': new_rule.operator.value,
                    'threshold': new_rule.threshold,
                    'priority': new_rule.priority
                }
                
                content = f"Adaptive rule learned: {new_rule.name} - {new_rule.description}"
                
                self.store_memory(
                    content=json.dumps(rule_data),
                    memory_type="adaptive_rule",
                    metadata={
                        'rule_id': new_rule.rule_id,
                        'patterns_analyzed': len(market_patterns),
                        'success_rate': len(successful_patterns) / len(market_patterns)
                    }
                )
                
                self.logger.info(f"Learned new adaptive rule: {new_rule.name}")
                return new_rule
            
        except Exception as e:
            self.logger.error(f"Error learning adaptive rule: {e}")
        
        return None
    
    def _analyze_pattern_features(self, patterns: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns to find common features"""
        try:
            if not patterns:
                return {}
            
            # Calculate averages and ranges for numerical features
            features = {}
            
            # Collect all possible features
            all_keys = set()
            for pattern in patterns:
                all_keys.update(pattern.keys())
            
            for key in all_keys:
                values = [pattern.get(key) for pattern in patterns if pattern.get(key) is not None]
                
                if not values:
                    continue
                
                # Handle numerical values
                if all(isinstance(v, (int, float)) for v in values):
                    features[key] = {
                        'avg': np.mean(values),
                        'min': np.min(values),
                        'max': np.max(values),
                        'std': np.std(values),
                        'type': 'numerical'
                    }
                
                # Handle categorical values
                else:
                    value_counts = {}
                    for value in values:
                        value_counts[value] = value_counts.get(value, 0) + 1
                    
                    most_common = max(value_counts.items(), key=lambda x: x[1])
                    features[key] = {
                        'most_common': most_common[0],
                        'frequency': most_common[1] / len(values),
                        'type': 'categorical'
                    }
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error analyzing pattern features: {e}")
            return {}
    
    def _generate_adaptive_rule(self, features: Dict[str, Any]) -> Optional[TradingRule]:
        """Generate a new rule based on analyzed features"""
        try:
            # Find the most predictive feature
            best_feature = None
            best_score = 0
            
            for feature_name, feature_data in features.items():
                if feature_data['type'] == 'numerical':
                    # Score based on consistency (low standard deviation relative to mean)
                    if feature_data['avg'] != 0:
                        score = 1 / (1 + feature_data['std'] / abs(feature_data['avg']))
                        if score > best_score:
                            best_score = score
                            best_feature = (feature_name, feature_data)
                
                elif feature_data['type'] == 'categorical':
                    # Score based on frequency of most common value
                    if feature_data['frequency'] > best_score:
                        best_score = feature_data['frequency']
                        best_feature = (feature_name, feature_data)
            
            if not best_feature or best_score < 0.7:
                return None
            
            feature_name, feature_data = best_feature
            
            # Generate rule based on feature type
            rule_id = f"adaptive_{feature_name}_{int(time.time())}"
            
            if feature_data['type'] == 'numerical':
                # Create threshold-based rule
                threshold = feature_data['avg']
                operator = RuleOperator.GREATER_THAN
                
                # Determine if above or below average is better
                if feature_data['avg'] > feature_data['min'] + (feature_data['max'] - feature_data['min']) * 0.7:
                    operator = RuleOperator.GREATER_THAN
                else:
                    operator = RuleOperator.LESS_THAN
                
                condition = f"{feature_name} {operator.value} {threshold:.3f}"
                
            else:
                # Create equality-based rule
                threshold = 0  # Not used for categorical
                operator = RuleOperator.EQUAL
                condition = f"{feature_name} == '{feature_data['most_common']}'"
            
            new_rule = TradingRule(
                rule_id=rule_id,
                rule_type=RuleType.ENTRY,  # Default to entry rule
                name=f"Adaptive {feature_name.title()} Rule",
                description=f"Learned rule based on {feature_name} patterns",
                condition=condition,
                parameters={'feature': feature_name, 'learned': True},
                operator=operator,
                threshold=threshold if feature_data['type'] == 'numerical' else 0,
                priority=3,  # Lower priority for adaptive rules
                enabled=True
            )
            
            return new_rule
            
        except Exception as e:
            self.logger.error(f"Error generating adaptive rule: {e}")
            return None
    
    async def record_rule_outcome(self, rule_id: str, symbol: str, success: bool, profit_loss: float = 0.0):
        """Record the outcome of a rule trigger"""
        try:
            if rule_id not in self.rules:
                self.logger.warning(f"Rule {rule_id} not found for outcome recording")
                return
            
            rule = self.rules[rule_id]
            rule.update_performance(success)
            
            # Learn from outcome using base agent method
            decision = f"Rule trigger: {rule.name} for {symbol}"
            outcome = f"Result: {'success' if success else 'failure'} with P&L ${profit_loss:.2f}"
            
            self.learn_from_outcome(decision, outcome, success, profit_loss)
            
            # Store rule performance update
            content = f"Rule outcome: {rule.name} for {symbol} - {'SUCCESS' if success else 'FAILURE'}"
            
            metadata = {
                'rule_id': rule_id,
                'symbol': symbol,
                'success': success,
                'profit_loss': profit_loss,
                'success_count': rule.success_count,
                'failure_count': rule.failure_count,
                'accuracy': rule.accuracy,
                'last_triggered': rule.last_triggered.isoformat() if rule.last_triggered else None
            }
            
            self.store_memory(content, "rule_performance", metadata)
            
            # Disable rule if performance is consistently poor
            if rule.success_count + rule.failure_count >= 20 and rule.accuracy < 0.3:
                rule.enabled = False
                self.logger.warning(f"Disabled rule {rule.name} due to poor performance ({rule.accuracy:.1%})")
            
            self.logger.info(f"Recorded rule outcome: {rule.name} {'SUCCESS' if success else 'FAILURE'} (Accuracy: {rule.accuracy:.1%})")
            
        except Exception as e:
            self.logger.error(f"Error recording rule outcome: {e}")
    
    async def get_rule_overview(self) -> Dict:
        """Get comprehensive rule overview"""
        try:
            rule_stats = {}
            
            for rule_type in RuleType:
                type_rules = [rule for rule in self.rules.values() if rule.rule_type == rule_type]
                
                if type_rules:
                    total_rules = len(type_rules)
                    enabled_rules = len([r for r in type_rules if r.enabled])
                    avg_accuracy = np.mean([r.accuracy for r in type_rules if r.success_count + r.failure_count > 0])
                    
                    rule_stats[rule_type.value] = {
                        'total_rules': total_rules,
                        'enabled_rules': enabled_rules,
                        'avg_accuracy': avg_accuracy if not np.isnan(avg_accuracy) else 0.0,
                        'rules': [
                            {
                                'id': rule.rule_id,
                                'name': rule.name,
                                'enabled': rule.enabled,
                                'accuracy': rule.accuracy,
                                'total_triggers': rule.success_count + rule.failure_count
                            }
                            for rule in type_rules
                        ]
                    }
            
            return {
                'agent_status': self.get_agent_state(),
                'rule_statistics': rule_stats,
                'total_rules': len(self.rules),
                'enabled_rules': len([r for r in self.rules.values() if r.enabled]),
                'adaptive_learning': self.adaptive_learning,
                'rule_sets': {
                    name: {
                        'enabled': rule_set.enabled,
                        'logic': rule_set.logic.value,
                        'success_rate': rule_set.get_success_rate(),
                        'rule_count': len(rule_set.rules)
                    }
                    for name, rule_set in self.rule_sets.items()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting rule overview: {e}")
            return {}
    
    async def process(self):
        """Main rule agent processing loop"""
        while self.is_active:
            try:
                # Update status
                enabled_rules = len([r for r in self.rules.values() if r.enabled])
                self.update_status(f"Monitoring {enabled_rules} active rules")
                
                # Analyze rule performance
                total_evaluations = sum(r.success_count + r.failure_count for r in self.rules.values())
                avg_accuracy = np.mean([r.accuracy for r in self.rules.values() if r.success_count + r.failure_count > 0])
                
                if not np.isnan(avg_accuracy):
                    self.logger.info(f"Rule system performance: {avg_accuracy:.1%} accuracy over {total_evaluations} evaluations")
                
                # Store periodic performance summary
                if total_evaluations > 0:
                    content = f"Rule system summary: {enabled_rules} active rules with {avg_accuracy:.1%} average accuracy"
                    
                    self.store_memory(
                        content=content,
                        memory_type="system_performance",
                        metadata={
                            'total_rules': len(self.rules),
                            'enabled_rules': enabled_rules,
                            'total_evaluations': total_evaluations,
                            'avg_accuracy': avg_accuracy if not np.isnan(avg_accuracy) else 0.0
                        }
                    )
                
                # Wait before next cycle
                await asyncio.sleep(600)  # 10 minutes
                
            except Exception as e:
                self.logger.error(f"Error in rule agent main loop: {e}")
                await asyncio.sleep(60)

# Example usage
if __name__ == "__main__":
    async def main():
        agent = RuleSetAgent()
        await agent.start()
        
        # Test rule evaluation
        market_data = {
            'price': 150.0,
            'volume': 2000000,
            'avg_volume': 1000000,
            'rsi': 75,
            'ema_20': 148.0,
            'vwap': 149.0,
            'volatility': 0.25
        }
        
        evaluations = await agent.evaluate_rules("AAPL", market_data, RuleType.ENTRY)
        
        for evaluation in evaluations:
            print(f"\nRule Evaluation:")
            print(f"  Rule: {evaluation.rule_id}")
            print(f"  Symbol: {evaluation.symbol}")
            print(f"  Triggered: {evaluation.triggered}")
            print(f"  Confidence: {evaluation.confidence:.1%}")
            print(f"  Reasoning: {evaluation.reasoning}")
        
        # Get overview
        overview = await agent.get_rule_overview()
        print(f"\nRule Overview:")
        print(f"  Total Rules: {overview.get('total_rules', 0)}")
        print(f"  Enabled Rules: {overview.get('enabled_rules', 0)}")
        print(f"  Adaptive Learning: {overview.get('adaptive_learning', False)}")
        
        await agent.stop()
    
    asyncio.run(main())
