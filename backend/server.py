# backend/server.py
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio

app = FastAPI()

# in-memory settings & dummy vector store
live_settings = {"scanInterval": 300, "symbols": ["GPRO","IXHL"]}
vector_store = {"hello": ["world"]}

class Settings(BaseModel):
    scanInterval: int | None
    symbols: list[str] | None

@app.get("/api/feed")
async def get_feed():
    # TODO: hook in your GremlinScanner results
    return [{"symbol":"GPRO","price":2.15,"up_pct":112.0}]

@app.get("/api/settings")
async def get_settings():
    return live_settings

@app.post("/api/settings")
async def post_settings(s: Settings):
    if s.scanInterval is not None:
        live_settings["scanInterval"] = s.scanInterval
    if s.symbols is not None:
        live_settings["symbols"] = s.symbols
    return live_settings

@app.get("/api/memory")
async def query_memory(q: str = ""):
    # dummy vector query
    return vector_store.get(q, [])

# optional: live websocket for pushes
@app.websocket("/ws/updates")
async def websocket_updates(ws: WebSocket):
    await ws.accept()
    while True:
        # send a heartbeat or new data
        await ws.send_json({"type":"ping"})
        await asyncio.sleep(live_settings["scanInterval"])

