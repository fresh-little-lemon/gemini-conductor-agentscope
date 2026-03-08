from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import os
from .event_bus import EventSink
from .event_types import RunEvent
from .session_index import SessionIndexer
from .control_hub import ControlHub

app = FastAPI()

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

event_sink = EventSink()
control_hub = ControlHub()
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

@app.websocket("/control")
async def websocket_control(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            cmd = data.get("type")
            payload = data.get("payload", {})
            
            if cmd == "agent.pause":
                await control_hub.pause(payload.get("agentId"))
            elif cmd == "agent.resume":
                await control_hub.resume(payload.get("agentId"))
            elif cmd == "viewer.lock":
                await event_sink.emit(RunEvent(
                    type="viewer.lock_state", 
                    payload={"tabId": payload.get("tabId"), "locked": True}
                ))
            elif cmd == "viewer.unlock":
                await event_sink.emit(RunEvent(
                    type="viewer.lock_state", 
                    payload={"tabId": payload.get("tabId"), "locked": False}
                ))
            elif cmd == "viewer.input":
                agent_id = payload.get("tabId")
                if agent_id:
                    await control_hub.log_operation(agent_id, payload)
                
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
