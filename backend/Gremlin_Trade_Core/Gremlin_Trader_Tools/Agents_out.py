#!/usr/bin/env python3
"""
Agent Output Handler - Receives all data from all agents properly, manages it, 
and distributes to logs and embedder and strategy set creation
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from Gremlin_Trade_Core.globals import (
    logger, setup_module_logger, CFG, MEM,
    LOGS_DIR, STRATEGIES_DIR, METADATA_DB_PATH, embed_text
)

# Import memory system components
from Gremlin_Trade_Memory.embedder import store_embedding, package_embedding
from Gremlin_Trade_Memory.Agent_in import send_data_to_agent, get_memory_system_status

# Setup module logger
agents_out_logger = setup_module_logger("agents", "output_handler")

# Output file paths
AGENT_LOGS_FILE = LOGS_DIR / "Agents.out"
STRATEGY_OUTPUT_FILE = STRATEGIES_DIR / "Generated_Strategies.jsonl"
PERFORMANCE_LOG_FILE = LOGS_DIR / "Performance_Metrics.jsonl"

class AgentOutputHandler:
    """Handles all agent outputs and distributes them appropriately"""
    
    def __init__(self):
        self.log_buffer = []
        self.strategy_buffer = []
        self.performance_buffer = []
        self.memory_integration_buffer = []
        
        # Ensure output directories exist
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        STRATEGIES_DIR.mkdir(parents=True, exist_ok=True)
        
        # Communication stats
        self.communication_stats = {
            'total_logs_processed': 0,
            'memory_embeddings_created': 0,
            'agent_notifications_sent': 0,
            'errors': 0
        }
    
    def process_agent_logs(self, log_entries: List[Dict[str, Any]]):
        """Process logs from all agents with enhanced memory integration"""
        try:
            for entry in log_entries:
                # Add processing timestamp
                entry["processed_at"] = datetime.now(timezone.utc).isoformat()
                
                # Categorize and route the log entry
                self._categorize_log_entry(entry)
                
                # Create memory embedding for important entries
                self._create_memory_embedding(entry)
                
                # Send data to relevant agents via Agent_in
                self._notify_relevant_agents(entry)
                
                # Add to general log buffer
                self.log_buffer.append(entry)
                
                self.communication_stats['total_logs_processed'] += 1
            
            # Flush logs to file
            self._flush_logs()
            
            agents_out_logger.info(f"Processed {len(log_entries)} log entries with memory integration")
            
        except Exception as e:
            self.communication_stats['errors'] += 1
            agents_out_logger.error(f"Error processing agent logs: {e}")
    
    def _categorize_log_entry(self, entry: Dict[str, Any]):
        """Categorize log entry and route to appropriate buffer"""
        try:
            entry_type = entry.get("type", "general")
            
            # Route based on entry type
            if entry_type in ["signal", "trade", "position"]:
                self._process_trading_entry(entry)
            elif entry_type == "strategy":
                self._process_strategy_entry(entry)
            elif entry_type == "performance":
                self._process_performance_entry(entry)
            elif entry_type == "error":
                self._process_error_entry(entry)
            
        except Exception as e:
            agents_out_logger.error(f"Error categorizing log entry: {e}")
    
    def _process_trading_entry(self, entry: Dict[str, Any]):
        """Process trading-related log entries"""
        try:
            # Extract trading data
            trading_data = {
                "timestamp": entry.get("timestamp"),
                "symbol": entry.get("symbol"),
                "action": entry.get("action"),
                "price": entry.get("price"),
                "volume": entry.get("volume"),
                "signal_type": entry.get("signal_type"),
                "confidence": entry.get("confidence"),
                "metadata": entry
            }
            
            # Store in database
            self._store_trading_data(trading_data)
            
            # Generate strategy insights
            self._generate_strategy_insights(trading_data)
            
            agents_out_logger.debug(f"Processed trading entry: {entry.get('symbol')}")
            
        except Exception as e:
            agents_out_logger.error(f"Error processing trading entry: {e}")
    
    def _process_strategy_entry(self, entry: Dict[str, Any]):
        """Process strategy-related log entries"""
        try:
            strategy_data = {
                "timestamp": entry.get("timestamp"),
                "strategy_name": entry.get("strategy_name"),
                "parameters": entry.get("parameters"),
                "performance": entry.get("performance"),
                "signals_generated": entry.get("signals_generated"),
                "success_rate": entry.get("success_rate"),
                "metadata": entry
            }
            
            self.strategy_buffer.append(strategy_data)
            agents_out_logger.debug(f"Processed strategy entry: {strategy_data.get('strategy_name')}")
            
        except Exception as e:
            agents_out_logger.error(f"Error processing strategy entry: {e}")
    
    def _process_performance_entry(self, entry: Dict[str, Any]):
        """Process performance-related log entries"""
        try:
            performance_data = {
                "timestamp": entry.get("timestamp"),
                "metric_type": entry.get("metric_type"),
                "value": entry.get("value"),
                "period": entry.get("period"),
                "benchmark": entry.get("benchmark"),
                "metadata": entry
            }
            
            self.performance_buffer.append(performance_data)
            agents_out_logger.debug(f"Processed performance entry: {performance_data.get('metric_type')}")
            
        except Exception as e:
            agents_out_logger.error(f"Error processing performance entry: {e}")
    
    def _process_error_entry(self, entry: Dict[str, Any]):
        """Process error-related log entries"""
        try:
            # Log errors with high priority
            error_data = {
                "timestamp": entry.get("timestamp"),
                "error_type": entry.get("error_type"),
                "message": entry.get("message"),
                "stack_trace": entry.get("stack_trace"),
                "component": entry.get("component"),
                "severity": entry.get("severity", "medium")
            }
            
            # Log to main logger
            if error_data["severity"] == "high":
                agents_out_logger.error(f"HIGH SEVERITY ERROR: {error_data['message']}")
            else:
                agents_out_logger.warning(f"ERROR: {error_data['message']}")
            
        except Exception as e:
            agents_out_logger.error(f"Error processing error entry: {e}")
    
    def _store_trading_data(self, trading_data: Dict[str, Any]):
        """Store trading data in metadata database"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(METADATA_DB_PATH)
            cursor = conn.cursor()
            
            # Insert signal data
            if trading_data.get("signal_type"):
                cursor.execute('''
                    INSERT OR REPLACE INTO signals 
                    (id, symbol, signal_type, confidence, price, volume, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f"{trading_data['symbol']}_{trading_data['timestamp']}",
                    trading_data.get("symbol"),
                    trading_data.get("signal_type"),
                    trading_data.get("confidence"),
                    trading_data.get("price"),
                    trading_data.get("volume"),
                    trading_data.get("timestamp"),
                    json.dumps(trading_data.get("metadata", {}))
                ))
            
            # Insert trade data
            if trading_data.get("action"):
                cursor.execute('''
                    INSERT OR REPLACE INTO trades 
                    (id, symbol, action, quantity, price, timestamp, pnl, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f"{trading_data['symbol']}_{trading_data['timestamp']}_{trading_data['action']}",
                    trading_data.get("symbol"),
                    trading_data.get("action"),
                    trading_data.get("volume", 0),
                    trading_data.get("price"),
                    trading_data.get("timestamp"),
                    0.0,  # PnL will be calculated later
                    json.dumps(trading_data.get("metadata", {}))
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            agents_out_logger.error(f"Error storing trading data: {e}")
    
    def _generate_strategy_insights(self, trading_data: Dict[str, Any]):
        """Generate strategy insights from trading data"""
        try:
            # Analyze patterns and generate insights
            insights = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "symbol": trading_data.get("symbol"),
                "pattern_type": self._identify_pattern(trading_data),
                "success_probability": self._calculate_success_probability(trading_data),
                "risk_level": self._assess_risk_level(trading_data),
                "recommended_action": self._recommend_action(trading_data)
            }
            
            # Store insights for strategy generation
            self.strategy_buffer.append(insights)
            
        except Exception as e:
            agents_out_logger.error(f"Error generating strategy insights: {e}")
    
    def _identify_pattern(self, trading_data: Dict[str, Any]) -> str:
        """Identify trading pattern from data"""
        try:
            signal_type = trading_data.get("signal_type", "")
            
            if "ema_cross" in signal_type:
                return "momentum_breakout"
            elif "vwap_break" in signal_type:
                return "vwap_breakout"
            elif "volume_spike" in signal_type:
                return "volume_surge"
            else:
                return "unknown_pattern"
                
        except Exception as e:
            agents_out_logger.error(f"Error identifying pattern: {e}")
            return "error_pattern"
    
    def _calculate_success_probability(self, trading_data: Dict[str, Any]) -> float:
        """Calculate success probability based on historical data"""
        try:
            confidence = trading_data.get("confidence", 0.5)
            volume = trading_data.get("volume", 0)
            
            # Simple probability calculation based on confidence and volume
            base_probability = confidence
            volume_boost = min(volume / 1000000, 0.3)  # Max 30% boost from volume
            
            return min(base_probability + volume_boost, 0.95)
            
        except Exception as e:
            agents_out_logger.error(f"Error calculating success probability: {e}")
            return 0.5
    
    def _assess_risk_level(self, trading_data: Dict[str, Any]) -> str:
        """Assess risk level of trading opportunity"""
        try:
            price = trading_data.get("price", 0)
            volume = trading_data.get("volume", 0)
            confidence = trading_data.get("confidence", 0.5)
            
            risk_score = 0
            
            # Price risk
            if price > 5.0:
                risk_score += 0.3
            elif price < 1.0:
                risk_score += 0.4
            
            # Volume risk
            if volume < 500000:
                risk_score += 0.3
            
            # Confidence risk
            if confidence < 0.3:
                risk_score += 0.4
            
            if risk_score > 0.7:
                return "high"
            elif risk_score > 0.4:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            agents_out_logger.error(f"Error assessing risk level: {e}")
            return "unknown"
    
    def _recommend_action(self, trading_data: Dict[str, Any]) -> str:
        """Recommend trading action based on analysis"""
        try:
            confidence = trading_data.get("confidence", 0.5)
            risk_level = self._assess_risk_level(trading_data)
            
            if confidence > 0.7 and risk_level == "low":
                return "strong_buy"
            elif confidence > 0.5 and risk_level in ["low", "medium"]:
                return "buy"
            elif confidence > 0.3:
                return "watch"
            else:
                return "avoid"
                
        except Exception as e:
            agents_out_logger.error(f"Error recommending action: {e}")
            return "hold"
                
    def _create_memory_embedding(self, entry: Dict[str, Any]):
        """Create memory embedding for important log entries"""
        try:
            entry_type = entry.get("type", "general")
            importance = self._calculate_entry_importance(entry)
            
            # Only create embeddings for important entries
            if importance < 0.3:
                return
            
            # Create text content for embedding
            content = self._generate_embedding_content(entry)
            
            # Generate embedding vector
            vector = embed_text(content)
            
            # Prepare metadata
            metadata = {
                'content_type': f'agent_log_{entry_type}',
                'source': 'agents_out',
                'original_entry': entry,
                'importance_score': importance,
                'agent_source': entry.get('agent_name', 'unknown'),
                'processing_timestamp': entry.get('processed_at')
            }
            
            # Create and store embedding
            embedding = package_embedding(content, vector, metadata)
            store_embedding(embedding)
            
            self.communication_stats['memory_embeddings_created'] += 1
            agents_out_logger.debug(f"Created memory embedding for {entry_type} entry with importance {importance:.2f}")
            
        except Exception as e:
            agents_out_logger.error(f"Error creating memory embedding: {e}")
    
    def _calculate_entry_importance(self, entry: Dict[str, Any]) -> float:
        """Calculate importance score for log entry"""
        try:
            importance = 0.1  # Base importance
            
            entry_type = entry.get("type", "general")
            
            # Type-based importance
            type_importance = {
                'signal': 0.8,
                'trade': 0.9,
                'position': 0.7,
                'strategy': 0.6,
                'performance': 0.7,
                'error': 0.5,
                'coordination_decision': 0.9
            }
            importance += type_importance.get(entry_type, 0.2)
            
            # Confidence-based importance
            confidence = entry.get("confidence", 0)
            if confidence > 0:
                importance += confidence * 0.3
            
            # Volume/price-based importance
            if entry.get("volume", 0) > 1000000:
                importance += 0.2
            
            if entry.get("price", 0) > 0:
                importance += 0.1
            
            # Error severity
            if entry_type == "error":
                severity = entry.get("severity", "medium")
                if severity == "high":
                    importance += 0.4
                elif severity == "critical":
                    importance += 0.6
            
            return min(1.0, importance)
            
        except Exception as e:
            agents_out_logger.error(f"Error calculating entry importance: {e}")
            return 0.5
    
    def _generate_embedding_content(self, entry: Dict[str, Any]) -> str:
        """Generate text content for embedding"""
        try:
            entry_type = entry.get("type", "general")
            
            if entry_type == "signal":
                return f"Trading signal for {entry.get('symbol', 'unknown')}: {entry.get('signal_type', 'unknown')} with {entry.get('confidence', 0):.2%} confidence at ${entry.get('price', 0):.2f}"
            
            elif entry_type == "trade":
                return f"Trade execution: {entry.get('action', 'unknown')} {entry.get('symbol', 'unknown')} at ${entry.get('price', 0):.2f} quantity {entry.get('quantity', 0)}"
            
            elif entry_type == "position":
                return f"Position update for {entry.get('symbol', 'unknown')}: {entry.get('quantity', 0)} shares with unrealized P&L ${entry.get('unrealized_pnl', 0):.2f}"
            
            elif entry_type == "strategy":
                return f"Strategy insight: {entry.get('strategy_name', 'unknown')} with {entry.get('success_rate', 0):.2%} success rate"
            
            elif entry_type == "performance":
                return f"Performance metric: {entry.get('metric_type', 'unknown')} = {entry.get('value', 'unknown')} for period {entry.get('period', 'unknown')}"
            
            elif entry_type == "error":
                return f"System error in {entry.get('component', 'unknown')}: {entry.get('message', 'unknown error')}"
            
            else:
                # Generic content generation
                return f"Agent log entry: {entry_type} from {entry.get('agent_name', 'unknown')} - {entry.get('message', str(entry))}"
            
        except Exception as e:
            agents_out_logger.error(f"Error generating embedding content: {e}")
            return f"Log entry: {entry.get('type', 'unknown')} - {str(entry)[:100]}"
    
    def _notify_relevant_agents(self, entry: Dict[str, Any]):
        """Notify relevant agents of new data via Agent_in"""
        try:
            entry_type = entry.get("type", "general")
            source_agent = entry.get("agent_name", "unknown")
            
            # Determine which agents should be notified
            relevant_agents = self._determine_relevant_agents(entry_type, entry)
            
            for agent_name in relevant_agents:
                if agent_name != source_agent:  # Don't notify the source agent
                    try:
                        notification_data = {
                            'query_type': entry_type,
                            'context': {
                                'symbol': entry.get('symbol'),
                                'signal_type': entry.get('signal_type'),
                                'confidence': entry.get('confidence'),
                                'source_agent': source_agent,
                                'timestamp': entry.get('timestamp')
                            },
                            'entry_summary': entry
                        }
                        
                        success = send_data_to_agent(agent_name, notification_data)
                        if success:
                            self.communication_stats['agent_notifications_sent'] += 1
                        
                    except Exception as e:
                        agents_out_logger.error(f"Error notifying {agent_name}: {e}")
            
        except Exception as e:
            agents_out_logger.error(f"Error notifying relevant agents: {e}")
    
    def _determine_relevant_agents(self, entry_type: str, entry: Dict[str, Any]) -> List[str]:
        """Determine which agents should be notified of this entry"""
        try:
            relevant_agents = []
            
            if entry_type == "signal":
                relevant_agents.extend(["strategy_agent", "rule_agent", "risk_agent", "timing_agent"])
            
            elif entry_type == "trade":
                relevant_agents.extend(["portfolio_tracker", "tax_estimator", "performance_tracker"])
            
            elif entry_type == "position":
                relevant_agents.extend(["risk_agent", "portfolio_tracker"])
            
            elif entry_type == "strategy":
                relevant_agents.extend(["coordinator", "performance_tracker"])
            
            elif entry_type == "performance":
                relevant_agents.extend(["coordinator", "strategy_agent"])
            
            elif entry_type == "error":
                relevant_agents.extend(["runtime_agent", "coordinator"])
            
            # Always notify coordinator for important events
            if entry.get("confidence", 0) > 0.7 or entry_type in ["trade", "error"]:
                relevant_agents.append("coordinator")
            
            return list(set(relevant_agents))  # Remove duplicates
            
        except Exception as e:
            agents_out_logger.error(f"Error determining relevant agents: {e}")
            return []
    
    def _flush_logs(self):
        """Flush all log buffers to files"""
        try:
            # Flush general logs
            if self.log_buffer:
                with open(AGENT_LOGS_FILE, "a") as f:
                    for entry in self.log_buffer:
                        f.write(json.dumps(entry) + "\n")
                self.log_buffer.clear()
            
            # Flush strategy data
            if self.strategy_buffer:
                with open(STRATEGY_OUTPUT_FILE, "a") as f:
                    for entry in self.strategy_buffer:
                        f.write(json.dumps(entry) + "\n")
                self.strategy_buffer.clear()
            
            # Flush performance data
            if self.performance_buffer:
                with open(PERFORMANCE_LOG_FILE, "a") as f:
                    for entry in self.performance_buffer:
                        f.write(json.dumps(entry) + "\n")
                self.performance_buffer.clear()
            
        except Exception as e:
            agents_out_logger.error(f"Error flushing logs: {e}")
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent log entries"""
        try:
            if not AGENT_LOGS_FILE.exists():
                return []
            
            logs = []
            with open(AGENT_LOGS_FILE, "r") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        logs.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
            
            return logs
            
        except Exception as e:
            agents_out_logger.error(f"Error getting recent logs: {e}")
            return []
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        try:
            if not PERFORMANCE_LOG_FILE.exists():
                return {}
            
            metrics = {}
            with open(PERFORMANCE_LOG_FILE, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        metric_type = entry.get("metric_type")
                        if metric_type:
                            metrics[metric_type] = entry
                    except json.JSONDecodeError:
                        continue
            
            return metrics
            
        except Exception as e:
            agents_out_logger.error(f"Error getting performance summary: {e}")
            return {}
            
    def get_communication_statistics(self) -> Dict[str, Any]:
        """Get statistics about agent communication and memory integration"""
        try:
            # Get memory system status
            memory_status = get_memory_system_status()
            
            return {
                'agents_out_stats': self.communication_stats,
                'memory_system_status': memory_status,
                'buffer_sizes': {
                    'log_buffer': len(self.log_buffer),
                    'strategy_buffer': len(self.strategy_buffer),
                    'performance_buffer': len(self.performance_buffer),
                    'memory_integration_buffer': len(self.memory_integration_buffer)
                },
                'recent_activity': {
                    'logs_in_buffer': len(self.log_buffer),
                    'total_processed': self.communication_stats['total_logs_processed']
                }
            }
            
        except Exception as e:
            agents_out_logger.error(f"Error getting communication statistics: {e}")
            return {'error': str(e)}

        except Exception as e:
            agents_out_logger.error(f"Error recommending action: {e}")
            return "hold"

# Global output handler instance
output_handler = AgentOutputHandler()

# Export main functions
def process_agent_logs(log_entries: List[Dict[str, Any]]):
    """Process logs from agents with memory integration"""
    return output_handler.process_agent_logs(log_entries)

def get_recent_logs(limit: int = 100) -> List[Dict[str, Any]]:
    """Get recent log entries"""
    return output_handler.get_recent_logs(limit)

def get_performance_summary() -> Dict[str, Any]:
    """Get performance summary"""
    return output_handler.get_performance_summary()

def get_communication_statistics() -> Dict[str, Any]:
    """Get agent communication and memory integration statistics"""
    return output_handler.get_communication_statistics()

def flush_all_buffers():
    """Flush all buffers to files"""
    output_handler._flush_logs()

# Initialize on import
try:
    agents_out_logger.info("Agent output handler initialized")
except Exception as e:
    agents_out_logger.error(f"Error initializing agent output handler: {e}")

if __name__ == "__main__":
    pass
