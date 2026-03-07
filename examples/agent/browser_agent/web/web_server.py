from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from .event_bus import EventSink
from .event_types import RunEvent

app = FastAPI()

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

event_sink = EventSink()

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
