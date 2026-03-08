from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import asyncio
import json
import os
import uuid
from .event_bus import EventSink
from .event_types import RunEvent
from .session_index import SessionIndexer
from .control_hub import ControlHub
from orchestrator import Orchestrator

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

@app.post("/run")
async def start_run(background_tasks: BackgroundTasks, html_path: str = "html_0210/100.html"):
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    
    # Run orchestrator in background
    async def run_orchestrator():
        # We need to use the absolute path for html_path
        abs_html_path = os.path.abspath(html_path)
        
        orch = Orchestrator()
        await orch.run(
            html_path=abs_html_path,
            run_id=run_id,
            event_sink=event_sink,
            control_hub=control_hub
        )
        await event_sink.emit(RunEvent(type="run.done", runId=run_id))

    background_tasks.add_task(run_orchestrator)
    return {"runId": run_id}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/sessions")
async def list_sessions():
    return indexer.list_sessions()

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    details = indexer.get_session_details(session_id)
    if not details:
        raise HTTPException(status_code=404, detail="Session not found")
    return details

@app.get("/files")
async def get_file(path: str):
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(os.path.abspath(SESSIONS_DIR)):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(abs_path)
