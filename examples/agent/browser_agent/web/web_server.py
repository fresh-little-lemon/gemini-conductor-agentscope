from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import os
from .event_bus import EventSink
from .event_types import RunEvent
from .session_index import SessionIndexer

app = FastAPI()

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

event_sink = EventSink()
# Use absolute path for sessions directory
SESSIONS_DIR = os.path.join(os.getcwd(), "sessions")
indexer = SessionIndexer(SESSIONS_DIR)

@app.websocket("/events")
async def websocket_events(websocket: WebSocket):
    await websocket.accept()
    try:
        async for event in event_sink.subscribe():
            await websocket.send_json(event.model_dump())
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/sessions")
async def list_sessions():
    return indexer.list_sessions()
