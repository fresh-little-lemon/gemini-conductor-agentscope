import pytest
from fastapi.testclient import TestClient
from web.web_server import app, event_sink
from web.event_types import RunEvent
import json
import asyncio

def test_websocket_broadcast():
    client = TestClient(app)
    with client.websocket_connect("/events") as websocket:
        # Emit an event via event_sink
        event = RunEvent(type="test.event", payload={"foo": "bar"})
        
        # We need to run the emit in the same event loop as the server if possible, 
        # but TestClient's websocket_connect is a bit different.
        # Actually, event_sink.emit will put it into queues that the websocket handler is listening to.
        
        async def emit_event():
            await event_sink.emit(event)
            
        loop = asyncio.get_event_loop()
        loop.run_until_complete(emit_event())
        
        data = websocket.receive_json()
        assert data["type"] == "test.event"
        assert data["payload"]["foo"] == "bar"
