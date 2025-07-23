#!/usr/bin/env python3
"""
Central Agent Configuration and Coordination
Sends logs to Agent.out for logging and sends all memory data to the embedder.
Fully analyzes all scripts and intended purposes from the architecture, using centralized imports through globals.py
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.Gremlin_Trade_Core.globals import (
    CFG, MEM, logger, setup_module_logger,
    embed_text, package_embedding,
    recursive_scan, run_scanner,
    get_live_penny_stocks, apply_signal_rules,
    METADATA_DB_PATH, CHROMA_DB_PATH
)

# Agent configuration and coordination
agent_logger = setup_module_logger("agents", "coordinator")

class AgentCoordinator:
    """Central coordinator for all trading agents"""
    
    def __init__(self):
        self.agents = {}
        self.active_scans = {}
        self.memory_queue = []
        self.log_queue = []
        
    def initialize_agents(self):
        """Initialize all trading agents"""
        try:
            agent_logger.info("Initializing trading agents...")
            
            # Initialize IBKR agent
            if CFG.get("agents", {}).get("ibkr", {}).get("enabled", True):
                self.initialize_ibkr_agent()
            
            # Initialize scanner agent
            if CFG.get("agents", {}).get("scanner", {}).get("enabled", True):
                self.initialize_scanner_agent()
            
            # Initialize strategy agent
            self.initialize_strategy_agent()
            
            # Initialize memory agent
            self.initialize_memory_agent()
            
            # Initialize risk management agent
            self.initialize_risk_agent()
            
            agent_logger.info("All agents initialized successfully")
            
        except Exception as e:
            agent_logger.error(f"Error initializing agents: {e}")
    
    def initialize_ibkr_agent(self):
        """Initialize Interactive Brokers agent"""
        try:
            from backend.Gremlin_Trade_Core.Gremlin_Trader_Tools.Trade_Agent.IBKR_API_trader import IBKRAgent
            
            ibkr_config = CFG.get("agents", {}).get("ibkr", {})
            self.agents["ibkr"] = IBKRAgent(ibkr_config)
            agent_logger.info("IBKR agent initialized")
            
        except ImportError:
            agent_logger.warning("IBKR agent not available - check ib_insync installation")
        except Exception as e:
            agent_logger.error(f"Error initializing IBKR agent: {e}")
    
    def initialize_scanner_agent(self):
        """Initialize scanner agent for penny stock detection"""
        try:
            from backend.Gremlin_Trade_Core.Gremlin_Trader_Tools.Strategy_Agent.signal_generator import generate_signals
            
            self.agents["scanner"] = {
                "generate_signals": generate_signals,
                "config": CFG.get("agents", {}).get("scanner", {}),
                "active": True
            }
            agent_logger.info("Scanner agent initialized")
            
        except Exception as e:
            agent_logger.error(f"Error initializing scanner agent: {e}")
    
    def initialize_strategy_agent(self):
        """Initialize strategy agent"""
        try:
            self.agents["strategy"] = {
                "config": CFG.get("strategy", {}),
                "active_strategies": [],
                "performance_metrics": {}
            }
            agent_logger.info("Strategy agent initialized")
            
        except Exception as e:
            agent_logger.error(f"Error initializing strategy agent: {e}")
    
    def initialize_memory_agent(self):
        """Initialize memory and embedding agent"""
        try:
            from backend.Gremlin_Trade_Memory.embedder import package_embedding, get_all_embeddings
            
            self.agents["memory"] = {
                "embedder": package_embedding,
                "retriever": get_all_embeddings,
                "config": MEM,
                "active": True
            }
            agent_logger.info("Memory agent initialized")
            
        except Exception as e:
            agent_logger.error(f"Error initializing memory agent: {e}")
    
    def initialize_risk_agent(self):
        """Initialize risk management agent"""
        try:
            risk_config = CFG.get("agents", {}).get("risk_management", {})
            self.agents["risk"] = {
                "config": risk_config,
                "active_positions": {},
                "risk_metrics": {},
                "active": True
            }
            agent_logger.info("Risk management agent initialized")
            
        except Exception as e:
            agent_logger.error(f"Error initializing risk agent: {e}")
    
    def run_coordinated_scan(self):
        """Run coordinated scanning across all timeframes"""
        try:
            agent_logger.info("Starting coordinated scan...")
            
            # Get scanner configuration
            scanner_config = CFG.get("agents", {}).get("scanner", {})
            strategy_config = CFG.get("strategy", {})
            
            # Get symbols to scan
            symbols = ["GPRO", "IXHL", "SAVA", "BBIG", "PROG", "ATER"]  # Example symbols
            timeframes = scanner_config.get("timeframes", ["1min", "5min", "15min"])
            
            # Run recursive scanning
            if strategy_config.get("recursive_scanning", {}).get("enabled", True):
                hits = recursive_scan(symbols, timeframes)
            else:
                hits = run_scanner(symbols)
            
            # Process hits
            for hit in hits:
                self.process_signal(hit)
            
            agent_logger.info(f"Coordinated scan complete - {len(hits)} signals found")
            return hits
            
        except Exception as e:
            agent_logger.error(f"Error in coordinated scan: {e}")
            return []
    
    def process_signal(self, signal):
        """Process and route signal to appropriate agents"""
        try:
            # Log the signal
            self.log_signal(signal)
            
            # Store in memory
            self.store_signal_memory(signal)
            
            # Evaluate with risk management
            self.evaluate_risk(signal)
            
            # Send to strategy evaluation
            self.evaluate_strategy(signal)
            
        except Exception as e:
            agent_logger.error(f"Error processing signal: {e}")
    
    def log_signal(self, signal):
        """Log signal to Agent.out"""
        try:
            log_entry = {
                "timestamp": signal.get("timestamp"),
                "symbol": signal.get("symbol"),
                "signal_type": signal.get("signal", []),
                "confidence": signal.get("confidence"),
                "price": signal.get("price"),
                "volume": signal.get("volume")
            }
            self.log_queue.append(log_entry)
            agent_logger.info(f"Signal logged: {signal.get('symbol')} - {signal.get('signal', [])}")
            
        except Exception as e:
            agent_logger.error(f"Error logging signal: {e}")
    
    def store_signal_memory(self, signal):
        """Store signal in memory/embedder"""
        try:
            # Create text summary for embedding
            summary = f"{signal.get('symbol')} signal: {', '.join(signal.get('signal', []))} at ${signal.get('price', 0):.2f}"
            
            # Generate embedding
            vector = embed_text(summary)
            
            # Package with metadata
            embedding = package_embedding(
                text=summary,
                vector=vector,
                meta={
                    "symbol": signal.get("symbol"),
                    "signal_type": signal.get("signal", []),
                    "confidence": signal.get("confidence"),
                    "price": signal.get("price"),
                    "volume": signal.get("volume"),
                    "timeframe": signal.get("timeframe"),
                    "timestamp": signal.get("timestamp"),
                    "source": "agent_coordinator"
                }
            )
            
            self.memory_queue.append(embedding)
            agent_logger.info(f"Signal stored in memory: {signal.get('symbol')}")
            
        except Exception as e:
            agent_logger.error(f"Error storing signal memory: {e}")
    
    def evaluate_risk(self, signal):
        """Evaluate signal with risk management"""
        try:
            if "risk" not in self.agents:
                return
            
            risk_config = self.agents["risk"]["config"]
            
            # Basic risk checks
            risk_score = 0
            
            # Price risk
            if signal.get("price", 0) > risk_config.get("max_price", 10.0):
                risk_score += 0.3
            
            # Volume risk
            if signal.get("volume", 0) < risk_config.get("min_volume", 1000000):
                risk_score += 0.2
            
            # Confidence risk
            if signal.get("confidence", 0) < 0.5:
                risk_score += 0.3
            
            signal["risk_score"] = risk_score
            agent_logger.info(f"Risk evaluation complete: {signal.get('symbol')} - Risk: {risk_score:.2f}")
            
        except Exception as e:
            agent_logger.error(f"Error in risk evaluation: {e}")
    
    def evaluate_strategy(self, signal):
        """Evaluate signal with strategy logic"""
        try:
            if "strategy" not in self.agents:
                return
            
            strategy_config = self.agents["strategy"]["config"]
            
            # Strategy scoring
            strategy_score = 0
            
            # EMA cross bonus
            if "ema_cross_bullish" in signal.get("signal", []):
                strategy_score += 0.3
            
            # VWAP break bonus
            if "vwap_break" in signal.get("signal", []):
                strategy_score += 0.2
            
            # Volume spike bonus
            if "volume_spike" in signal.get("signal", []):
                strategy_score += 0.3
            
            signal["strategy_score"] = strategy_score
            agent_logger.info(f"Strategy evaluation complete: {signal.get('symbol')} - Score: {strategy_score:.2f}")
            
        except Exception as e:
            agent_logger.error(f"Error in strategy evaluation: {e}")
    
    def flush_logs_to_output(self):
        """Flush all logs to Agent.out"""
        try:
            if not self.log_queue:
                return
            
            # Write logs to Agent.out file
            from backend.Gremlin_Trade_Core.Gremlin_Trader_Tools.Agents_out import process_agent_logs
            process_agent_logs(self.log_queue)
            
            # Clear queue
            self.log_queue.clear()
            agent_logger.info("Logs flushed to Agent.out")
            
        except Exception as e:
            agent_logger.error(f"Error flushing logs: {e}")
    
    def flush_memory_to_embedder(self):
        """Flush all memory to embedder"""
        try:
            if not self.memory_queue:
                return
            
            # Process memory queue
            from backend.Gremlin_Trade_Memory.embedder import store_embedding
            
            for embedding in self.memory_queue:
                store_embedding(embedding)
            
            # Clear queue
            self.memory_queue.clear()
            agent_logger.info("Memory flushed to embedder")
            
        except Exception as e:
            agent_logger.error(f"Error flushing memory: {e}")
    
    def get_system_status(self):
        """Get status of all agents"""
        try:
            status = {
                "agents": {},
                "active_scans": len(self.active_scans),
                "memory_queue_size": len(self.memory_queue),
                "log_queue_size": len(self.log_queue),
                "configuration": {
                    "ibkr_enabled": "ibkr" in self.agents,
                    "scanner_enabled": "scanner" in self.agents,
                    "memory_enabled": "memory" in self.agents,
                    "risk_enabled": "risk" in self.agents
                }
            }
            
            for agent_name, agent in self.agents.items():
                status["agents"][agent_name] = {
                    "active": agent.get("active", False),
                    "config_loaded": "config" in agent
                }
            
            return status
            
        except Exception as e:
            agent_logger.error(f"Error getting system status: {e}")
            return {}

# Global coordinator instance
coordinator = AgentCoordinator()

# Initialize on import
try:
    coordinator.initialize_agents()
    agent_logger.info("Agent coordinator initialized successfully")
except Exception as e:
    agent_logger.error(f"Error initializing agent coordinator: {e}")

# Main execution functions
def run_scan():
    """Run a coordinated scan"""
    return coordinator.run_coordinated_scan()

def get_status():
    """Get system status"""
    return coordinator.get_system_status()

def flush_all():
    """Flush all queues"""
    coordinator.flush_logs_to_output()
    coordinator.flush_memory_to_embedder()

if __name__ == "__main__":
    # Run a test scan
    agent_logger.info("Running test scan...")
    hits = run_scan()
    agent_logger.info(f"Test scan complete - {len(hits)} hits")
    
    # Flush all data
    flush_all()
    
    # Show status
    status = get_status()
    agent_logger.info(f"System status: {status}")
