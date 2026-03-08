import pytest
import asyncio
import os
from web.chrome_launcher import ChromeLauncher
from web.cdp_bridge import CDPBridge
from web.event_bus import EventSink
from utils.mcp_utils import create_browser_client

@pytest.mark.asyncio
async def test_chrome_launch_and_cdp_capture():
    # 1. Find chrome path
    # We can use the logic from mcp_utils or just hardcode a common one for linux
    chrome_path = "/opt/google/chrome/chrome"
    if not os.path.exists(chrome_path):
        pytest.skip("Chrome not found at /opt/google/chrome/chrome")
        
    # 2. Launch Chrome
    launcher = ChromeLauncher(executable_path=chrome_path, headless=True)
    try:
        cdp_endpoint = launcher.launch()
        assert cdp_endpoint.startswith("http://localhost:")
        
        # 3. Setup CDPBridge
        sink = EventSink()
        bridge = CDPBridge(cdp_endpoint, sink)
        
        # 4. Connect and capture one frame
        await bridge.connect()
        
        frames = []
        async def collector():
            async for event in sink.subscribe():
                if event.type == "viewer.frame":
                    frames.append(event)
                    break
        
        collector_task = asyncio.create_task(collector())
        await bridge.start_streaming(fps=1)
        
        try:
            await asyncio.wait_for(collector_task, timeout=5.0)
        except asyncio.TimeoutError:
            pytest.fail("Failed to capture a frame within 5 seconds")
            
        assert len(frames) == 1
        assert "frame" in frames[0].payload
        assert len(frames[0].payload["frame"]) > 0
        
        await bridge.stop()
        
    finally:
        launcher.stop()
