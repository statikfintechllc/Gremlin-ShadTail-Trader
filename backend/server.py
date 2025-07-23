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
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import from centralized globals and modules
from backend.Gremlin_Trade_Core.globals import (
    CFG, MEM, logger, setup_module_logger,
    get_live_penny_stocks, recursive_scan
)

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

@app.get("/api/feed")
async def get_feed():
    """Get trading feed data with recursive scanning"""
    try:
        server_logger.info("Feed data requested")
        
        # Import signal generator
        from backend.Gremlin_Trade_Core.Gremlin_Trader_Tools.Strategy_Agent.signal_generator import generate_signals
        
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
            from backend.Gremlin_Trade_Core.globals import run_scanner
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
        
        from backend.Gremlin_Trade_Memory.embedder import query_embeddings, get_all_embeddings
        
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
        from backend.Gremlin_Trade_Core.config.Agent_in import get_status
        from backend.Gremlin_Trade_Memory.embedder import get_backend_status
        
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
        from backend.Gremlin_Trade_Core.Gremlin_Trader_Tools.Strategy_Agent.signal_generator import get_signal_performance_metrics
        from backend.Gremlin_Trade_Core.Gremlin_Trader_Tools.Agents_out import get_performance_summary
        
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
        from backend.Gremlin_Trade_Core.Gremlin_Trader_Tools.Strategy_Agent.signal_generator import generate_signals
        
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
        from backend.Gremlin_Trade_Core.config.Agent_in import coordinator
        server_logger.info("Agent coordinator initialized")
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

