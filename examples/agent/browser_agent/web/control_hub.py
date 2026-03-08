import asyncio
from typing import Dict, Optional

class ControlHub:
    """Manages agent states like pausing and resuming."""
    def __init__(self) -> None:
        self.paused_agents: Dict[str, asyncio.Event] = {}

    async def pause(self, agent_id: str) -> None:
        """Pause a specific agent."""
        if agent_id not in self.paused_agents:
            self.paused_agents[agent_id] = asyncio.Event()
            self.paused_agents[agent_id].set() # Ensure it exists as set if we pause it later
        self.paused_agents[agent_id].clear()

    async def resume(self, agent_id: str) -> None:
        """Resume a specific agent."""
        if agent_id not in self.paused_agents:
            self.paused_agents[agent_id] = asyncio.Event()
        self.paused_agents[agent_id].set()

    async def is_paused(self, agent_id: str) -> bool:
        """Check if an agent is paused."""
        if agent_id not in self.paused_agents:
            return False
        return not self.paused_agents[agent_id].is_set()

    async def wait_if_paused(self, agent_id: str) -> None:
        """Wait if the agent is paused."""
        if agent_id not in self.paused_agents:
            return # Not paused
        await self.paused_agents[agent_id].wait()

class AgentControlGate:
    """A wrapper for subagents to check if they should pause."""
    def __init__(self, hub: Optional[ControlHub], agent_id: str) -> None:
        self.hub = hub
        self.agent_id = agent_id

    async def wait_if_paused(self) -> None:
        """Wait if the hub says this agent is paused."""
        if self.hub:
            await self.hub.wait_if_paused(self.agent_id)
