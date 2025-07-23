# backend/server.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/gremlin_trader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('gremlin_trader')

app = FastAPI(title="Gremlin ShadTail Trader API", version="1.0.0")

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321", "http://127.0.0.1:4321"],  # Astro dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# in-memory settings & dummy vector store
live_settings = {"scanInterval": 300, "symbols": ["GPRO","IXHL"]}
vector_store = {"hello": ["world"]}

class Settings(BaseModel):
    scanInterval: int | None
    symbols: list[str] | None

@app.get("/api/feed")
async def get_feed():
    """Get trading feed data"""
    logger.info("Feed data requested")
    # TODO: hook in your GremlinScanner results
    feed_data = [{"symbol":"GPRO","price":2.15,"up_pct":112.0}]
    logger.debug(f"Returning feed data: {feed_data}")
    return feed_data

@app.get("/api/settings")
async def get_settings():
    """Get current settings"""
    logger.info("Settings requested")
    logger.debug(f"Current settings: {live_settings}")
    return live_settings

@app.post("/api/settings")
async def post_settings(s: Settings):
    """Update settings"""
    logger.info(f"Settings update requested: {s}")
    if s.scanInterval is not None:
        live_settings["scanInterval"] = s.scanInterval
        logger.info(f"Updated scan interval to {s.scanInterval}")
    if s.symbols is not None:
        live_settings["symbols"] = s.symbols
        logger.info(f"Updated symbols to {s.symbols}")
    logger.debug(f"New settings: {live_settings}")
    return live_settings

@app.get("/api/memory")
async def query_memory(q: str = ""):
    """Query vector memory store"""
    logger.info(f"Memory query: '{q}'")
    # dummy vector query
    result = vector_store.get(q, [])
    logger.debug(f"Memory query result: {result}")
    return result

# optional: live websocket for pushes
@app.websocket("/ws/updates")
async def websocket_updates(ws: WebSocket):
    """WebSocket endpoint for live updates"""
    await ws.accept()
    logger.info("WebSocket connection established")
    try:
        while True:
            # send a heartbeat or new data
            await ws.send_json({
                "type": "ping", 
                "timestamp": datetime.now().isoformat()
            })
            logger.debug("WebSocket heartbeat sent")
            await asyncio.sleep(live_settings["scanInterval"])
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info("WebSocket connection closed")

@app.on_event("startup")
async def startup_event():
    logger.info("Gremlin ShadTail Trader API starting up")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Gremlin ShadTail Trader API shutting down")

