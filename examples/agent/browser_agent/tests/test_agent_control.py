import pytest
import asyncio
from web.control_hub import ControlHub, AgentControlGate

@pytest.mark.asyncio
async def test_agent_control_gate_blocking():
    """Test that AgentControlGate correctly blocks and resumes."""
    hub = ControlHub()
    agent_id = "test_agent"
    gate = AgentControlGate(hub, agent_id)
    
    # 1. Initially should NOT block
    # We use wait_for to ensure it doesn't hang if there's a bug
    await asyncio.wait_for(gate.wait_if_paused(), timeout=0.1)
    
    # 2. Pause the agent
    await hub.pause(agent_id)
    
    # 3. wait_if_paused should now block
    wait_task = asyncio.create_task(gate.wait_if_paused())
    await asyncio.sleep(0.1)
    assert not wait_task.done()
    
    # 4. Resume the agent
    await hub.resume(agent_id)
    await asyncio.wait_for(wait_task, timeout=0.1)
    assert wait_task.done()

@pytest.mark.asyncio
async def test_agent_control_gate_no_hub():
    """Test that it handles cases where hub might be None (optional gating)."""
    gate = AgentControlGate(None, "id")
    # Should just pass through
    await asyncio.wait_for(gate.wait_if_paused(), timeout=0.1)
