#!/usr/bin/env python3
"""
Gremlin ShadTail Trader - Main System Startup
Complete trading system initialization with all agents and memory integration
"""

import asyncio
import signal
import sys
import logging
from pathlib import Path
from datetime import datetime
import json

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from Gremlin_Trade_Core.agent_coordinator import AgentCoordinator
from Gremlin_Trade_Core.Gremlin_Trader_Tools.Tool_Control_Agent.tool_control_agent import ToolControlAgent
from Gremlin_Trade_Core.Gremlin_Trader_Tools.Service_Agents.market_data_service import MarketDataService
from Gremlin_Trade_Core.Gremlin_Trader_Tools.Service_Agents.simple_market_service import SimpleMarketService

class GremlinTradingSystem:
    """
    Main trading system that coordinates all components
    """
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.agent_coordinator = None
        self.tool_control_agent = None
        self.market_data_service = None
        
        # System state
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        
        # Configuration
        self.config = {
            'trading_enabled': False,  # Start in paper trading mode
            'auto_start_agents': True,
            'enable_web_interface': True,
            'log_level': 'INFO',
            'market_data_provider': 'simple'  # or 'yahoo', 'alpaca', etc.
        }
        
        self.logger.info("Gremlin ShadTail Trader System initialized")
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = Path(__file__).parent / "Gremlin_Trade_Core" / "config" / "Gremlin_Trade_Logs"
        log_dir.mkdir(exist_ok=True)
        
        # Main system log
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "system_main.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Suppress noisy loggers
        logging.getLogger("chromadb").setLevel(logging.WARNING)
        logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    
    async def initialize_system(self):
        """Initialize all system components"""
        try:
            self.logger.info("Initializing Gremlin ShadTail Trader System...")
            
            # Initialize market data service first
            self.logger.info("Starting market data service...")
            if self.config['market_data_provider'] == 'simple':
                self.market_data_service = SimpleMarketService()
            else:
                self.market_data_service = MarketDataService()
            
            await self.market_data_service.start()
            
            # Initialize tool control agent
            self.logger.info("Starting tool control agent...")
            self.tool_control_agent = ToolControlAgent()
            await self.tool_control_agent.start()
            
            # Initialize agent coordinator (which will initialize all trading agents)
            self.logger.info("Starting agent coordinator...")
            self.agent_coordinator = AgentCoordinator()
            await self.agent_coordinator.start()
            await self.agent_coordinator.initialize_agents()
            
            self.is_running = True
            self.logger.info("Gremlin ShadTail Trader System fully initialized!")
            
            # Print system status
            await self.print_system_status()
            
        except Exception as e:
            self.logger.error(f"Error initializing system: {e}")
            await self.shutdown_system()
            raise
    
    async def print_system_status(self):
        """Print comprehensive system status"""
        try:
            print("\n" + "="*80)
            print("GREMLIN SHADTAIL TRADER - SYSTEM STATUS")
            print("="*80)
            
            # Agent Coordinator Status
            if self.agent_coordinator:
                coord_overview = await self.agent_coordinator.get_coordination_overview()
                print(f"\n📊 AGENT COORDINATOR:")
                print(f"   Status: {coord_overview.get('coordinator_status', {}).get('status', 'Unknown')}")
                print(f"   Mode: {coord_overview.get('coordination_mode', 'Unknown')}")
                print(f"   Phase: {coord_overview.get('trading_phase', 'Unknown')}")
                print(f"   Performance: {coord_overview.get('performance', {})}")
                print(f"   Watchlist: {len(coord_overview.get('active_watchlist', []))} symbols")
                
                # Individual Agent Status
                agent_overviews = coord_overview.get('agent_overviews', {})
                
                if 'timing' in agent_overviews:
                    timing = agent_overviews['timing']
                    print(f"\n⏰ TIMING AGENT:")
                    print(f"   Status: {timing.get('agent_status', {}).get('status', 'Unknown')}")
                    print(f"   Active Analyses: {timing.get('active_analyses', 0)}")
                    print(f"   Accuracy: {timing.get('timing_accuracy', 0.0):.2%}")
                
                if 'strategy' in agent_overviews:
                    strategy = agent_overviews['strategy']
                    print(f"\n📈 STRATEGY AGENT:")
                    print(f"   Status: {strategy.get('agent_status', {}).get('status', 'Unknown')}")
                    print(f"   Active Strategies: {strategy.get('active_strategies', 0)}")
                    print(f"   Performance: {strategy.get('performance', {})}")
                
                if 'rules' in agent_overviews:
                    rules = agent_overviews['rules']
                    print(f"\n📋 RULE SET AGENT:")
                    print(f"   Status: {rules.get('agent_status', {}).get('status', 'Unknown')}")
                    print(f"   Active Rules: {rules.get('total_rules', 0)}")
                    print(f"   Rule Sets: {rules.get('rule_sets', 0)}")
                
                if 'runtime' in agent_overviews:
                    runtime = agent_overviews['runtime']
                    print(f"\n⚙️ RUNTIME AGENT:")
                    print(f"   Status: {runtime.get('agent_status', {}).get('status', 'Unknown')}")
                    print(f"   Active Tasks: {runtime.get('active_tasks', 0)}")
                    print(f"   System Load: {runtime.get('system_metrics', {}).get('cpu_percent', 0):.1f}% CPU")
            
            # Tool Control Agent Status
            if self.tool_control_agent:
                tool_overview = await self.tool_control_agent.get_tool_overview()
                print(f"\n🔧 TOOL CONTROL AGENT:")
                print(f"   Status: {tool_overview.get('agent_status', {}).get('status', 'Unknown')}")
                print(f"   Total Tools: {tool_overview.get('total_tools', 0)}")
                print(f"   Active Tools: {tool_overview.get('status_distribution', {}).get('active', 0)}")
                print(f"   Success Rate: {tool_overview.get('performance_summary', {}).get('success_rate', 0.0):.2%}")
            
            # Market Data Service Status
            print(f"\n💹 MARKET DATA SERVICE:")
            print(f"   Provider: {self.config['market_data_provider']}")
            print(f"   Status: {'Active' if self.market_data_service else 'Inactive'}")
            
            # System Configuration
            print(f"\n⚙️ SYSTEM CONFIGURATION:")
            print(f"   Trading Mode: {'LIVE' if self.config['trading_enabled'] else 'PAPER'}")
            print(f"   Auto Start: {self.config['auto_start_agents']}")
            print(f"   Web Interface: {self.config['enable_web_interface']}")
            print(f"   Log Level: {self.config['log_level']}")
            
            print("\n" + "="*80)
            print("🚀 SYSTEM READY - All agents initialized and running!")
            print("💡 Use Ctrl+C to shutdown gracefully")
            print("="*80 + "\n")
            
        except Exception as e:
            self.logger.error(f"Error printing system status: {e}")
    
    async def start_trading_cycle(self):
        """Start the main trading cycle"""
        try:
            self.logger.info("Starting main trading cycle...")
            
            while self.is_running and not self.shutdown_event.is_set():
                try:
                    # Execute coordinated trading
                    if self.agent_coordinator:
                        await self.agent_coordinator.execute_coordinated_trading()
                    
                    # Wait before next cycle (30 minutes)
                    await asyncio.wait_for(
                        self.shutdown_event.wait(), 
                        timeout=1800
                    )
                    
                except asyncio.TimeoutError:
                    # Normal timeout, continue trading cycle
                    continue
                except Exception as e:
                    self.logger.error(f"Error in trading cycle: {e}")
                    await asyncio.sleep(300)  # 5 minutes on error
            
            self.logger.info("Trading cycle stopped")
            
        except Exception as e:
            self.logger.error(f"Fatal error in trading cycle: {e}")
            await self.shutdown_system()
    
    async def shutdown_system(self):
        """Gracefully shutdown all system components"""
        try:
            self.logger.info("Shutting down Gremlin ShadTail Trader System...")
            self.is_running = False
            self.shutdown_event.set()
            
            # Shutdown in reverse order of initialization
            if self.agent_coordinator:
                self.logger.info("Shutting down agent coordinator...")
                await self.agent_coordinator.shutdown_agents()
                await self.agent_coordinator.stop()
            
            if self.tool_control_agent:
                self.logger.info("Shutting down tool control agent...")
                await self.tool_control_agent.stop()
            
            if self.market_data_service:
                self.logger.info("Shutting down market data service...")
                await self.market_data_service.stop()
            
            self.logger.info("Gremlin ShadTail Trader System shutdown complete!")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown_system())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self):
        """Main system run method"""
        try:
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Initialize system
            await self.initialize_system()
            
            # Start main trading cycle
            await self.start_trading_cycle()
            
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Fatal system error: {e}")
        finally:
            await self.shutdown_system()

async def main():
    """Main entry point"""
    print("🎯 Starting Gremlin ShadTail Trader...")
    print("📊 Advanced AI-Powered Trading System")
    print("🧠 Memory-Enhanced Agent Architecture")
    print("-" * 50)
    
    system = GremlinTradingSystem()
    await system.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Gremlin ShadTail Trader shutdown complete!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
