import asyncio
import aiohttp
import websockets
import json
import base64
from typing import Optional, Dict, Any
from .event_bus import EventSink
from .event_types import RunEvent
from agentscope._logging import logger

class CDPBridge:
    """Bridges CDP (Chrome DevTools Protocol) to our event system for viewing/interaction."""
    
    def __init__(self, cdp_endpoint: str, event_sink: EventSink, tab_id: Optional[str] = None) -> None:
        self.cdp_endpoint = cdp_endpoint # e.g. http://localhost:9222
        self.event_sink = event_sink
        self.tab_id = tab_id
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.is_running = False
        self._msg_id = 0
        self._loop_task: Optional[asyncio.Task] = None
        self.fps = 5

    async def _get_ws_url(self) -> str:
        """Fetch the WebSocket URL for the target tab."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.cdp_endpoint}/json/list") as resp:
                targets = await resp.json()
                if not targets:
                    raise RuntimeError("No browser targets found.")
                
                # If tab_id is specified, find it. Otherwise take the first "page" target.
                target = None
                if self.tab_id:
                    for t in targets:
                        if t.get("id") == self.tab_id:
                            target = t
                            break
                else:
                    for t in targets:
                        if t.get("type") == "page":
                            target = t
                            break
                
                if not target:
                    raise RuntimeError(f"Target tab not found (tab_id={self.tab_id}).")
                
                return target["webSocketDebuggerUrl"]

    async def connect(self) -> None:
        """Connect to the CDP WebSocket."""
        ws_url = await self._get_ws_url()
        self.ws = await websockets.connect(ws_url)
        logger.info(f"CDPBridge connected to {ws_url}")
        
        # Enable Page domain to capture screenshots
        await self._send_command("Page.enable")
        # Enable Input domain to forward events
        await self._send_command("Input.enable")

    async def _send_command(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Send a command to CDP and wait for the response."""
        if not self.ws:
            raise RuntimeError("CDPBridge is not connected.")
        
        self._msg_id += 1
        msg = {
            "id": self._msg_id,
            "method": method,
            "params": params or {}
        }
        await self.ws.send(json.dumps(msg))
        
        # In a real implementation, we'd wait for the specific response ID.
        # For simplicity in this bridge, we assume commands are handled.
        # A more robust version would use a future-per-id map.
        return None

    async def start_streaming(self, fps: Optional[int] = None) -> None:
        """Start the screenshot streaming loop."""
        if fps:
            self.fps = fps
        self.is_running = True
        self._loop_task = asyncio.create_task(self._streaming_loop())
        logger.info(f"CDPBridge started streaming at {self.fps} FPS")

    async def _streaming_loop(self) -> None:
        """Periodically capture screenshots and emit events."""
        interval = 1.0 / self.fps
        while self.is_running:
            try:
                # Capture screenshot
                # params = {"format": "jpeg", "quality": 50} for speed
                self._msg_id += 1
                cmd_id = self._msg_id
                msg = {
                    "id": cmd_id,
                    "method": "Page.captureScreenshot",
                    "params": {"format": "jpeg", "quality": 50}
                }
                await self.ws.send(json.dumps(msg))
                
                # Wait for response
                while True:
                    resp_str = await self.ws.recv()
                    resp = json.loads(resp_str)
                    if resp.get("id") == cmd_id:
                        img_data = resp.get("result", {}).get("data")
                        if img_data:
                            await self.event_sink.emit(RunEvent(
                                type="viewer.frame",
                                payload={
                                    "frame": img_data,
                                    "tabId": self.tab_id or "default"
                                }
                            ))
                        break
                    # We might receive other events here (e.g. Page.loadEventFired)
                    # For now we ignore them.
                    
            except Exception as e:
                logger.error(f"CDPBridge streaming error: {e}")
                await asyncio.sleep(1)
            
            await asyncio.sleep(interval)

    async def stop(self) -> None:
        """Stop streaming and disconnect."""
        self.is_running = False
        if self._loop_task:
            self._loop_task.cancel()
        if self.ws:
            await self.ws.close()
            self.ws = None
        logger.info("CDPBridge stopped.")

    async def handle_input(self, input_event: Dict[str, Any]) -> None:
        """Forward user input from the viewer to the browser."""
        # input_event structure matches RunEvent payload for 'viewer.input'
        # e.g. {"action": "mousedown", "x": 100, "y": 200, "button": "left"}
        action = input_event.get("action")
        if action in ["mousedown", "mouseup", "mousemove"]:
            await self._send_command("Input.dispatchMouseEvent", {
                "type": action,
                "x": input_event.get("x", 0),
                "y": input_event.get("y", 0),
                "button": input_event.get("button", "left"),
                "clickCount": 1
            })
        elif action in ["keydown", "keyup"]:
            await self._send_command("Input.dispatchKeyEvent", {
                "type": action,
                "text": input_event.get("text"),
                "key": input_event.get("key"),
                # ... other key params if needed
            })
