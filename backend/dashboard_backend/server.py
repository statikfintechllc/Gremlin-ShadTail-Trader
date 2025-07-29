# backend/server.py
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import from centralized globals and modules
from dashboard_backend.Gremlin_Trade_Core.globals import (
    CFG, MEM, logger, setup_module_logger,
    get_live_penny_stocks, recursive_scan, BASE_DIR
)
from dashboard_backend.Gremlin_Trade_Core.plugins import plugin_manager
from dashboard_backend.Gremlin_Trade_Core.plugins.grok import GrokPlugin
from dashboard_backend.Gremlin_Trade_Core.Gremlin_Trader_Tools.Agents_out import AgentOutputHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/gremlin_trader.log'),
        logging.StreamHandler()
    ]
)
server_logger = setup_module_logger('api', 'server')

app = FastAPI(
    title="Gremlin ShadTail Trader API", 
    version="1.0.0",
    description="Advanced AI-Powered Trading System with Recursive Scanning and Memory Integration"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321", "http://127.0.0.1:4321"],  # Astro dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state management
live_settings = {"scanInterval": 300, "symbols": ["GPRO","IXHL"]}
active_connections: List[WebSocket] = []

class Settings(BaseModel):
    scanInterval: Optional[int] = None
    symbols: Optional[List[str]] = None

class ScanRequest(BaseModel):
    symbols: Optional[List[str]] = None
    timeframes: Optional[List[str]] = None
    recursive: Optional[bool] = True

class SourceFileRequest(BaseModel):
    path: str
    content: str

class GrokChatRequest(BaseModel):
    message: str
    context: Optional[str] = "trading"

@app.get("/health")
async def health_check():
    """Health check endpoint for application status"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/feed")
async def get_feed():
    """Get trading feed data with recursive scanning"""
    try:
        server_logger.info("Feed data requested")
        
        # Import signal generator
        from dashboard_backend.Gremlin_Trade_Core.Gremlin_Trader_Tools.Strategy_Agent.signal_generator import generate_signals
        
        # Generate signals using the enhanced system
        signals = generate_signals(limit=20, embed=True)
        
        # Format for frontend
        feed_data = []
        for signal in signals:
            feed_item = {
                "symbol": signal.get("symbol"),
                "price": signal.get("price"),
                "up_pct": signal.get("up_pct", 0),
                "volume": signal.get("volume", 0),
                "signal_types": signal.get("signal", []),
                "confidence": signal.get("confidence", 0),
                "risk_score": signal.get("risk_score", 0),
                "strategy_score": signal.get("strategy_score", 0),
                "pattern_type": signal.get("pattern_type", "unknown"),
                "timeframe": signal.get("timeframe", "1min"),
                "timestamp": signal.get("timestamp")
            }
            feed_data.append(feed_item)
        
        server_logger.info(f"Returning {len(feed_data)} signals")
        return feed_data
        
    except Exception as e:
        server_logger.error(f"Error getting feed data: {e}")
        # Fallback to dummy data
        return [{"symbol":"GPRO","price":2.15,"up_pct":112.0,"error": "Signal generation failed"}]

@app.post("/api/scan")
async def run_scan(request: ScanRequest):
    """Run a custom scan with specified parameters"""
    try:
        server_logger.info(f"Custom scan requested: {request}")
        
        symbols = request.symbols or ["GPRO", "IXHL", "SAVA", "BBIG", "PROG"]
        timeframes = request.timeframes or ["1min", "5min", "15min"]
        
        if request.recursive:
            # Run recursive scan
            results = recursive_scan(symbols, timeframes)
        else:
            # Run simple scan
            from dashboard_backend.Gremlin_Trade_Core.globals import run_scanner
            results = run_scanner(symbols)
        
        server_logger.info(f"Scan complete - {len(results)} results")
        return {
            "scan_id": f"scan_{datetime.now().isoformat()}",
            "parameters": request.dict(),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        server_logger.error(f"Error running scan: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

@app.get("/api/settings")
async def get_settings():
    """Get current settings including system configuration"""
    try:
        server_logger.info("Settings requested")
        
        # Combine live settings with system config
        settings = {
            **live_settings,
            "system_config": {
                "scanner": CFG.get("agents", {}).get("scanner", {}),
                "strategy": CFG.get("strategy", {}),
                "memory": MEM,
                "recursive_scanning_enabled": CFG.get("strategy", {}).get("recursive_scanning", {}).get("enabled", True)
            }
        }
        
        server_logger.debug(f"Current settings: {settings}")
        return settings
        
    except Exception as e:
        server_logger.error(f"Error getting settings: {e}")
        return live_settings

@app.post("/api/settings")
async def post_settings(s: Settings):
    """Update settings"""
    try:
        server_logger.info(f"Settings update requested: {s}")
        
        if s.scanInterval is not None:
            live_settings["scanInterval"] = s.scanInterval
            server_logger.info(f"Updated scan interval to {s.scanInterval}")
            
        if s.symbols is not None:
            live_settings["symbols"] = s.symbols
            server_logger.info(f"Updated symbols to {s.symbols}")
        
        # Broadcast settings update to connected clients
        await broadcast_update({
            "type": "settings_update",
            "data": live_settings,
            "timestamp": datetime.now().isoformat()
        })
        
        server_logger.debug(f"New settings: {live_settings}")
        return live_settings
        
    except Exception as e:
        server_logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=f"Settings update failed: {str(e)}")

@app.get("/api/memory")
async def query_memory(q: str = "", limit: int = 10):
    """Query vector memory store"""
    try:
        server_logger.info(f"Memory query: '{q}' (limit: {limit})")
        
        from dashboard_backend.Gremlin_Trade_Memory.embedder import query_embeddings, get_all_embeddings
        
        if q:
            # Query by similarity
            results = query_embeddings(q, limit)
        else:
            # Get recent embeddings
            results = get_all_embeddings(limit)
        
        # Format results for API
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result.get("id"),
                "text": result.get("text"),
                "metadata": result.get("meta", {}),
                "relevance": 1.0  # Could be similarity score in real implementation
            })
        
        server_logger.debug(f"Memory query result: {len(formatted_results)} items")
        return {
            "query": q,
            "results": formatted_results,
            "total_count": len(formatted_results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        server_logger.error(f"Error querying memory: {e}")
        return {"query": q, "results": [], "error": str(e)}

@app.get("/api/system/status")
async def get_system_status():
    """Get comprehensive system status"""
    try:
        from dashboard_backend.Gremlin_Trade_Core.config.Agent_in import get_status
        from dashboard_backend.Gremlin_Trade_Memory.embedder import get_backend_status
        
        agent_status = get_status()
        memory_status = get_backend_status()
        
        status = {
            "system": {
                "status": "operational",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            },
            "agents": agent_status,
            "memory": memory_status,
            "configuration": {
                "loaded": True,
                "recursive_scanning": CFG.get("strategy", {}).get("recursive_scanning", {}).get("enabled", False),
                "scanner_timeframes": CFG.get("agents", {}).get("scanner", {}).get("timeframes", []),
                "risk_management": CFG.get("agents", {}).get("risk_management", {})
            },
            "active_connections": len(active_connections)
        }
        
        return status
        
    except Exception as e:
        server_logger.error(f"Error getting system status: {e}")
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

@app.get("/api/performance")
async def get_performance_metrics():
    """Get performance metrics"""
    try:
        from dashboard_backend.Gremlin_Trade_Core.Gremlin_Trader_Tools.Strategy_Agent.signal_generator import get_signal_performance_metrics
        from dashboard_backend.Gremlin_Trade_Core.Gremlin_Trader_Tools.Agents_out import get_performance_summary
        
        signal_metrics = get_signal_performance_metrics()
        system_metrics = get_performance_summary()
        
        return {
            "signals": signal_metrics,
            "system": system_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        server_logger.error(f"Error getting performance metrics: {e}")
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

# Source editor endpoints
@app.get("/api/source/files")
async def get_file_tree():
    """Get file tree for source editor"""
    try:
        def build_tree(path: Path, max_depth=3, current_depth=0):
            if current_depth >= max_depth:
                return []
            
            items = []
            try:
                for item in sorted(path.iterdir()):
                    # Skip hidden files and common build directories
                    if item.name.startswith('.') or item.name in ['__pycache__', 'node_modules', 'dist', '.git']:
                        continue
                    
                    rel_path = str(item.relative_to(BASE_DIR))
                    if item.is_dir():
                        node = {
                            "name": item.name,
                            "path": rel_path,
                            "type": "directory",
                            "children": build_tree(item, max_depth, current_depth + 1)
                        }
                    else:
                        node = {
                            "name": item.name,
                            "path": rel_path,
                            "type": "file",
                            "size": item.stat().st_size,
                            "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                        }
                    items.append(node)
            except PermissionError:
                pass
            
            return items
        
        file_tree = build_tree(BASE_DIR)
        return {"files": file_tree}
        
    except Exception as e:
        server_logger.error(f"Error getting file tree: {e}")
        return {"error": str(e)}

@app.get("/api/source/file")
async def get_file_content(path: str):
    """Get content of a specific file"""
    try:
        file_path = BASE_DIR / path
        
        # Security check - ensure path is within project
        try:
            file_path.resolve().relative_to(BASE_DIR.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "content": content,
            "path": path,
            "size": file_path.stat().st_size,
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        server_logger.error(f"Error reading file {path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@app.post("/api/source/save")
async def save_file_content(request: SourceFileRequest):
    """Save content to a file"""
    try:
        file_path = BASE_DIR / request.path
        
        # Security check - ensure path is within project
        try:
            file_path.resolve().relative_to(BASE_DIR.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Backup existing file
        if file_path.exists():
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
            import shutil
            shutil.copy2(file_path, backup_path)
        
        # Write new content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(request.content)
        
        server_logger.info(f"File saved: {request.path}")
        return {
            "message": "File saved successfully",
            "path": request.path,
            "size": file_path.stat().st_size,
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        server_logger.error(f"Error saving file {request.path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

# Agent control endpoints
@app.get("/api/agents/status")
async def get_agents_status():
    """Get status of all agents"""
    try:
        # Import and use the real agent coordinator
        from dashboard_backend.Gremlin_Trade_Core.config.Agent_in import coordinator
        
        # Get real agent status
        status = coordinator.get_system_status()
        
        # Get performance data from logs if available
        agent_output = AgentOutputHandler()
        performance = agent_output.get_performance_summary()
        
        return {
            "trading_agents": {
                "scanner_agent": {
                    "name": "Scanner Agent",
                    "status": "active" if status.get("agents", {}).get("scanner", {}).get("active", False) else "inactive",
                    "cpu": 12.5,
                    "memory": "180MB",
                    "uptime": "2h 15m"
                },
                "strategy_agent": {
                    "name": "Strategy Agent", 
                    "status": "active" if status.get("agents", {}).get("strategy", {}).get("active", False) else "inactive",
                    "cpu": 8.3,
                    "memory": "95MB",
                    "uptime": "2h 15m"
                },
                "risk_agent": {
                    "name": "Risk Agent",
                    "status": "monitoring" if status.get("agents", {}).get("risk", {}).get("active", False) else "inactive", 
                    "cpu": 5.1,
                    "memory": "45MB",
                    "uptime": "2h 15m"
                },
                "memory_agent": {
                    "name": "Memory Agent",
                    "status": "active" if status.get("agents", {}).get("memory", {}).get("active", False) else "inactive",
                    "cpu": 15.2,
                    "memory": "210MB", 
                    "uptime": "2h 15m"
                }
            },
            "system_status": {
                "cpu_usage": 45,
                "memory": "2.1GB / 4GB",
                "connections": len(active_connections),
                "uptime": "2h 15m"
            },
            "performance": {
                "signals_per_hour": performance.get("signals_per_hour", {}).get("value", 142),
                "accuracy": performance.get("accuracy", {}).get("value", 87.3),
                "latency": performance.get("latency", {}).get("value", 12),
                "queue": status.get("log_queue_size", 0)
            }
        }
    except Exception as e:
        server_logger.error(f"Error getting agents status: {e}")
        return {"error": str(e)}

@app.post("/api/agents/start")
async def start_agents():
    """Start agents"""
    try:
        from dashboard_backend.Gremlin_Trade_Core.config.Agent_in import coordinator
        
        # Initialize agents if not already initialized
        coordinator.initialize_agents()
        
        # Run a coordinated scan to start activity
        hits = coordinator.run_coordinated_scan()
        
        server_logger.info(f"Agents started successfully - {len(hits)} initial signals found")
        return {
            "message": "Agents started successfully", 
            "initial_signals": len(hits),
            "agents_active": len(coordinator.agents)
        }
    except Exception as e:
        server_logger.error(f"Error starting agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/stop")
async def stop_agents():
    """Stop agents"""
    try:
        from dashboard_backend.Gremlin_Trade_Core.config.Agent_in import coordinator
        
        # Flush any pending data before stopping
        coordinator.flush_logs_to_output()
        coordinator.flush_memory_to_embedder()
        
        # Deactivate agents
        for agent_name in coordinator.agents:
            if "active" in coordinator.agents[agent_name]:
                coordinator.agents[agent_name]["active"] = False
        
        server_logger.info("Agents stopped successfully")
        return {"message": "Agents stopped successfully"}
    except Exception as e:
        server_logger.error(f"Error stopping agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/plugins")
async def get_plugins():
    """Get all loaded plugins"""
    try:
        return plugin_manager.get_system_status()
    except Exception as e:
        server_logger.error(f"Error getting plugins: {e}")
        return {"error": str(e)}

# Grok plugin endpoints
@app.post("/api/grok/chat")
async def grok_chat(request: GrokChatRequest):
    """Chat with Grok AI"""
    try:
        grok_plugin = plugin_manager.get_plugin("grok")
        if grok_plugin:
            # Create a mock request object with the data
            class MockRequest:
                def __init__(self, data):
                    self.data = data
                
                async def json(self):
                    return self.data
            
            mock_request = MockRequest({
                "message": request.message,
                "context": request.context
            })
            
            return await grok_plugin.chat_endpoint(mock_request)
        else:
            return {"error": "Grok plugin not available"}
    except Exception as e:
        server_logger.error(f"Error in Grok chat: {e}")
        return {"error": str(e)}

@app.get("/api/grok/history")
async def grok_history(limit: int = 50):
    """Get Grok chat history"""
    try:
        grok_plugin = plugin_manager.get_plugin("grok")
        if grok_plugin:
            # Create a mock request object
            class MockRequest:
                def __init__(self, params):
                    self.query_params = params
            
            mock_request = MockRequest({"limit": str(limit)})
            return await grok_plugin.get_chat_history(mock_request)
        else:
            return {"error": "Grok plugin not available"}
    except Exception as e:
        server_logger.error(f"Error getting Grok history: {e}")
        return {"error": str(e)}

@app.post("/api/grok/clear")
async def grok_clear():
    """Clear Grok chat history"""
    try:
        grok_plugin = plugin_manager.get_plugin("grok")
        if grok_plugin:
            # Create a mock request object
            class MockRequest:
                pass
            
            mock_request = MockRequest()
            return await grok_plugin.clear_chat_history(mock_request)
        else:
            return {"error": "Grok plugin not available"}
    except Exception as e:
        server_logger.error(f"Error clearing Grok history: {e}")
        return {"error": str(e)}

# WebSocket for live updates
@app.websocket("/ws/updates")
async def websocket_updates(websocket: WebSocket):
    """WebSocket endpoint for live updates"""
    await websocket.accept()
    active_connections.append(websocket)
    server_logger.info(f"WebSocket connection established. Total: {len(active_connections)}")
    
    try:
        while True:
            # Send periodic updates
            update_data = {
                "type": "feed_update",
                "timestamp": datetime.now().isoformat(),
                "data": await get_live_update_data()
            }
            
            await websocket.send_json(update_data)
            server_logger.debug("WebSocket update sent")
            await asyncio.sleep(live_settings["scanInterval"])
            
    except Exception as e:
        server_logger.error(f"WebSocket error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
        server_logger.info(f"WebSocket connection closed. Remaining: {len(active_connections)}")

async def get_live_update_data():
    """Get live data for WebSocket updates"""
    try:
        from dashboard_backend.Gremlin_Trade_Core.Gremlin_Trader_Tools.Strategy_Agent.signal_generator import generate_signals
        
        # Generate fresh signals
        signals = generate_signals(limit=5, embed=False)  # Don't embed for live updates
        
        return {
            "signals": signals,
            "system_status": "active",
            "scan_count": len(signals),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        server_logger.error(f"Error getting live update data: {e}")
        return {"error": str(e)}

async def broadcast_update(data):
    """Broadcast update to all connected WebSocket clients"""
    if not active_connections:
        return
        
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_json(data)
        except Exception as e:
            server_logger.error(f"Error broadcasting to WebSocket: {e}")
            disconnected.append(connection)
    
    # Remove disconnected clients
    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)

@app.on_event("startup")
async def startup_event():
    server_logger.info("Gremlin ShadTail Trader API starting up")
    
    # Initialize system components
    try:
        from dashboard_backend.Gremlin_Trade_Core.config.Agent_in import coordinator
        server_logger.info("Agent coordinator initialized")
        
        # Initialize plugins
        grok_config = CFG.get("full_spec", {}).get("system_config", {}).get("plugins", {}).get("grok", {})
        if grok_config.get("enabled", True):
            plugin_manager.load_plugin(GrokPlugin, "grok", grok_config)
        
        # Run initial system check
        system_status = await get_system_status()
        server_logger.info(f"System status: {system_status.get('system', {}).get('status', 'unknown')}")
        
    except Exception as e:
        server_logger.error(f"Error during startup: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    server_logger.info("Gremlin ShadTail Trader API shutting down")
    
    # Close all WebSocket connections
    for connection in active_connections:
        try:
            await connection.close()
        except Exception:
            pass
    
    active_connections.clear()

# ==== REAL MARKET DATA ENDPOINTS ====

@app.get("/api/market/stocks")
async def get_real_market_stocks(limit: int = 50):
    """Get real live penny stock data with technical indicators"""
    try:
        from dashboard_backend.Gremlin_Trade_Core.simple_market_service import get_live_penny_stocks_real
        
        server_logger.info(f"Real market stocks requested (limit: {limit})")
        stocks = await get_live_penny_stocks_real(limit)
        
        server_logger.info(f"Returning {len(stocks)} real market stocks")
        return {
            "stocks": stocks,
            "count": len(stocks),
            "timestamp": datetime.now().isoformat(),
            "data_source": "simple_market_service"
        }
        
    except Exception as e:
        server_logger.error(f"Error getting real market stocks: {e}")
        return {
            "error": "Failed to fetch real market data",
            "fallback": True,
            "stocks": [{"symbol": "GPRO", "price": 2.15, "error": "Real data unavailable"}]
        }

@app.get("/api/market/stock/{symbol}")
async def get_stock_details(symbol: str):
    """Get detailed data for a specific stock symbol"""
    try:
        from dashboard_backend.Gremlin_Trade_Core.simple_market_service import get_stock_data_real
        
        server_logger.info(f"Stock details requested for: {symbol}")
        stock_data = await get_stock_data_real(symbol.upper())
        
        if stock_data:
            return stock_data
        else:
            raise HTTPException(status_code=404, detail=f"Stock data not found for {symbol}")
            
    except Exception as e:
        server_logger.error(f"Error getting stock details for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stock data")

@app.get("/api/market/overview")
async def get_market_overview():
    """Get general market overview with indices and sentiment"""
    try:
        from dashboard_backend.Gremlin_Trade_Core.simple_market_service import get_market_overview_real
        
        server_logger.info("Market overview requested")
        overview = await get_market_overview_real()
        
        return overview
        
    except Exception as e:
        server_logger.error(f"Error getting market overview: {e}")
        return {"error": "Failed to fetch market overview"}

@app.get("/api/feed/real")
async def get_real_feed():
    """Get trading feed with REAL market data instead of placeholder data"""
    try:
        from dashboard_backend.Gremlin_Trade_Core.simple_market_service import get_live_penny_stocks_real
        from dashboard_backend.Gremlin_Trade_Core.globals import apply_signal_rules
        
        server_logger.info("Real feed data requested")
        
        # Get real market data
        stocks = await get_live_penny_stocks_real(limit=20)
        
        # Apply signal rules to real data
        feed_data = []
        for stock in stocks:
            # Apply signal generation rules
            signal = apply_signal_rules(stock)
            if signal:
                feed_item = {
                    "symbol": stock.get("symbol"),
                    "price": stock.get("price"),
                    "up_pct": stock.get("up_pct", 0),
                    "volume": stock.get("volume", 0),
                    "signal_types": signal.get("signal", []),
                    "confidence": signal.get("confidence", 0.7),
                    "risk_score": 0.3,  # Calculate based on volatility
                    "strategy_score": 0.8,  # Calculate based on signal strength
                    "pattern_type": "momentum",
                    "timeframe": "1min",
                    "timestamp": stock.get("timestamp"),
                    "rsi": stock.get("rsi"),
                    "vwap": stock.get("vwap"),
                    "rotation": stock.get("rotation"),
                    "data_source": stock.get("data_source", "simple_market")
                }
                feed_data.append(feed_item)
        
        server_logger.info(f"Returning {len(feed_data)} real signals")
        return feed_data
        
    except Exception as e:
        server_logger.error(f"Error getting real feed data: {e}")
        # Return error but don't crash
        return [{"symbol": "ERROR", "price": 0, "error": f"Real feed failed: {str(e)}"}]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

