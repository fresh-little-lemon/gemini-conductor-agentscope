import subprocess
import socket
import time
import os
import sys
from typing import Optional, List
from agentscope._logging import logger

def find_free_port() -> int:
    """Find a free port on the local machine."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

class ChromeLauncher:
    """Launches Chrome with remote debugging enabled."""
    
    def __init__(
        self,
        executable_path: str,
        user_data_dir: Optional[str] = None,
        headless: bool = False,
        width: int = 1280,
        height: int = 720,
    ) -> None:
        self.executable_path = executable_path
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.width = width
        self.height = height
        self.process: Optional[subprocess.Popen] = None
        self.port: Optional[int] = None

    def launch(self) -> str:
        """Launch Chrome and return the CDP endpoint URL."""
        self.port = find_free_port()
        
        args = [
            self.executable_path,
            f"--remote-debugging-port={self.port}",
            f"--window-size={self.width},{self.height}",
            "--no-first-run",
            "--no-default-browser-check",
        ]
        
        if self.headless:
            args.append("--headless=new")
            
        if self.user_data_dir:
            args.append(f"--user-data-dir={self.user_data_dir}")
        else:
            # Use a temporary directory if not provided
            import tempfile
            self.temp_dir = tempfile.TemporaryDirectory(prefix="chrome_data_")
            args.append(f"--user-data-dir={self.temp_dir.name}")

        logger.info(f"Launching Chrome with CDP port {self.port}...")
        self.process = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        
        # Wait for the port to be available
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                with socket.create_connection(("localhost", self.port), timeout=1):
                    logger.info(f"Chrome launched successfully on port {self.port}")
                    return f"http://localhost:{self.port}"
            except (socket.timeout, ConnectionRefusedError):
                time.sleep(0.5)
        
        raise RuntimeError("Failed to launch Chrome or CDP port not available within timeout.")

    def stop(self) -> None:
        """Stop the Chrome process."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
        
        if hasattr(self, "temp_dir"):
            self.temp_dir.cleanup()
