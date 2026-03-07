import pytest
import asyncio
import json
from web.event_bus import EventSink
from web.event_types import RunEvent
from web.control_hub import ControlHub

@pytest.mark.asyncio
async def test_event_sink_collects_events():
    """Test that EventSink correctly emits events."""
    sink = EventSink()
    events = []

    async def event_collector():
        async for event in sink.subscribe():
            events.append(event)
            if len(events) == 2:
                break

    collector_task = asyncio.create_task(event_collector())
    
    # Give the collector task time to register its queue
    await asyncio.sleep(0.1)
    
    await sink.emit(RunEvent(type="test_event", payload={"data": 1}))
    await sink.emit(RunEvent(type="another_event", payload={"data": 2}))
    
    await asyncio.wait_for(collector_task, timeout=1.0)
    
    assert len(events) == 2
    assert events[0].type == "test_event"
    assert events[1].payload["data"] == 2

@pytest.mark.asyncio
async def test_control_hub_pause_resume():
    """Test that ControlHub correctly manages pause and resume."""
    hub = ControlHub()
    agent_id = "agent_1"
    
    # By default, it shouldn't be paused
    assert not await hub.is_paused(agent_id)
    
    await hub.pause(agent_id)
    assert await hub.is_paused(agent_id)
    
    # Check wait_if_paused
    wait_task = asyncio.create_task(hub.wait_if_paused(agent_id))
    
    # Wait a bit to ensure it's actually waiting
    await asyncio.sleep(0.1)
    assert not wait_task.done()
    
    await hub.resume(agent_id)
    await asyncio.wait_for(wait_task, timeout=0.5)
    assert not await hub.is_paused(agent_id)
