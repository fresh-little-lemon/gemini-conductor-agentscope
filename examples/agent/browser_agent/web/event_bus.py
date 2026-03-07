import asyncio
from typing import AsyncGenerator
from .event_types import RunEvent

class EventSink:
    """Central event emitter to handle system-wide events."""
    def __init__(self) -> None:
        self.subscribers: list[asyncio.Queue] = []

    async def emit(self, event: RunEvent) -> None:
        """Emit an event to all subscribers."""
        for queue in self.subscribers:
            await queue.put(event)

    async def subscribe(self) -> AsyncGenerator[RunEvent, None]:
        """Subscribe to events."""
        queue = asyncio.Queue()
        self.subscribers.append(queue)
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            self.subscribers.remove(queue)
