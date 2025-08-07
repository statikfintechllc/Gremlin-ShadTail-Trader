#!/usr/bin/env python3
"""
Simple test server to validate health check functionality without all dependencies
"""

from fastapi import FastAPI
from datetime import datetime
import uvicorn
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

app = FastAPI(
    title="Test Gremlin ShadTail Trader API", 
    version="1.0.0",
    description="Test server for health check validation"
)

@app.get("/health")
async def health_check():
    """Basic health check endpoint for application status"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/system/health")
async def comprehensive_health_check():
    """Comprehensive health check that validates all agent imports and initialization"""
    try:
        health_status = {
            "system": {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "mode": "test"
            },
            "agents": {
                "import_status": {},
                "initialization_status": {},
                "runtime_status": {}
            },
            "dependencies": {
                "fastapi": True,
                "uvicorn": True,
                "database": False,
                "memory_system": False
            },
            "configuration": {
                "loaded": True,
                "valid": True
            }
        }
        
        # Test critical agent imports - this validates that all modules can be loaded
        agent_imports = {
            "BaseMemoryAgent": "Gremlin_Trade_Core.Gremlin_Trader_Tools.Memory_Agent.base_memory_agent.BaseMemoryAgent",
            "MarketTimingAgent": "Gremlin_Trade_Core.Gremlin_Trader_Tools.Timing_Agent.market_timing.MarketTimingAgent", 
            "StrategyAgent": "Gremlin_Trade_Core.Gremlin_Trader_Tools.Strategy_Agent.strategy_agent.StrategyAgent",
            "RuleSetAgent": "Gremlin_Trade_Core.Gremlin_Trader_Tools.Rule_Set_Agent.rule_set_agent.RuleSetAgent",
            "RuntimeAgent": "Gremlin_Trade_Core.Gremlin_Trader_Tools.Run_Time_Agent.runtime_agent.RuntimeAgent",
            "MarketDataService": "Gremlin_Trade_Core.Gremlin_Trader_Tools.Service_Agents.market_data_service.MarketDataService",
            "SimpleMarketService": "Gremlin_Trade_Core.Gremlin_Trader_Tools.Service_Agents.simple_market_service.SimpleMarketService",
            "PortfolioTracker": "Gremlin_Trade_Core.Gremlin_Trader_Tools.Tool_Control_Agent.portfolio_tracker.PortfolioTracker",
            "ToolControlAgent": "Gremlin_Trade_Core.Gremlin_Trader_Tools.Tool_Control_Agent.tool_control_agent.ToolControlAgent",
            "SignalGenerator": "Gremlin_Trade_Core.Gremlin_Trader_Tools.Strategy_Agent.signal_generator.SignalGenerator",
            "RulesEngine": "Gremlin_Trade_Core.Gremlin_Trader_Tools.Rule_Set_Agent.rules_engine.RulesEngine",
            "TaxEstimator": "Gremlin_Trade_Core.Gremlin_Trader_Tools.Financial_Agent.tax_estimator.TaxEstimator",
            "StockScraper": "Gremlin_Trade_Core.Gremlin_Trader_Tools.Run_Time_Agent.stock_scraper.StockScraper",
            "AgentCoordinator": "Gremlin_Trade_Core.agent_coordinator.AgentCoordinator"
        }
        
        # Test each agent import
        for agent_name, import_path in agent_imports.items():
            try:
                # Dynamic import to validate the module
                module_parts = import_path.split('.')
                module_path = '.'.join(module_parts[:-1])
                class_name = module_parts[-1]
                
                module = __import__(module_path, fromlist=[class_name])
                agent_class = getattr(module, class_name)
                
                health_status["agents"]["import_status"][agent_name] = "success"
                print(f"✓ {agent_name} import successful")
                
            except Exception as e:
                health_status["agents"]["import_status"][agent_name] = f"failed: {str(e)}"
                print(f"✗ {agent_name} import failed: {e}")
                health_status["system"]["status"] = "degraded"
        
        # Calculate overall health score
        import_failures = sum(1 for status in health_status["agents"]["import_status"].values() 
                             if isinstance(status, str) and status.startswith("failed"))
        total_agents = len(health_status["agents"]["import_status"])
        
        if import_failures == 0:
            health_status["system"]["status"] = "healthy"
            health_status["system"]["health_score"] = 100
        elif import_failures <= total_agents * 0.2:  # Less than 20% failed
            health_status["system"]["status"] = "degraded"
            health_status["system"]["health_score"] = max(50, 100 - (import_failures * 10))
        else:
            health_status["system"]["status"] = "unhealthy"
            health_status["system"]["health_score"] = max(0, 50 - (import_failures * 5))
        
        health_status["summary"] = {
            "total_agents": total_agents,
            "successful_imports": total_agents - import_failures,
            "failed_imports": import_failures,
            "import_success_rate": ((total_agents - import_failures) / total_agents * 100) if total_agents > 0 else 0
        }
        
        print(f"Health check complete: {health_status['system']['status']} "
              f"({health_status['summary']['successful_imports']}/{total_agents} agents)")
        
        return health_status
        
    except Exception as e:
        print(f"Health check failed: {e}")
        return {
            "system": {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            "agents": {"import_status": {}, "initialization_status": {}, "runtime_status": {}},
            "dependencies": {},
            "configuration": {"loaded": False},
            "summary": {"error": "Health check system failure"}
        }

if __name__ == "__main__":
    print("🚀 Starting test server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")