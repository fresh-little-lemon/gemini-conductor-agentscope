# -*- coding: utf-8 -*-
"""MCP Utility for browser agent."""
import os
import json
import sys
import shutil
from typing import Optional, TYPE_CHECKING
from agentscope.mcp import StdIOStatefulClient
from agentscope._logging import logger

if TYPE_CHECKING:
    from utils.video_manager import VideoManager

def create_browser_client(
    headless: bool = False,
    video_manager: Optional["VideoManager"] = None,
    width: int = 1280,
    height: int = 720,
    isolated: bool = True,
    executable_path: Optional[str] = None,
    mcp_config_path: str = "configs/mcp_config.json",
    cdp_endpoint: Optional[str] = None,
) -> tuple[StdIOStatefulClient, str]:
    """
    Create a browser client with the specified configurations.
    
    Args:
        headless (bool): Whether to run the browser in headless mode.
        video_manager (VideoManager, optional): Video manager for recording.
        width (int): Viewport width. Default is 1280.
        height (int): Viewport height. Default is 720.
        isolated (bool): Whether to run in isolated mode (no shared profile).
                         Default is True.
        executable_path (str, optional): Path to the browser executable.
        mcp_config_path (str): Path to the MCP configuration file.
        cdp_endpoint (str, optional): CDP endpoint to connect to.
    
    Returns:
        tuple[StdIOStatefulClient, str]: 
            A tuple containing the initialized browser client and the actual executable path used.
    """
    # Load config if exists
    config = {}
    if os.path.exists(mcp_config_path):
        try:
            with open(mcp_config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Error loading MCP config from {mcp_config_path}: {e}")
            raise

    # Priority for executable_path with existence check: 
    # 1. CLI path (if exists)
    # 2. Config path (if exists)
    # 3. System Default (if exists)
    
    final_executable_path = None
    
    # 1. Check CLI path first
    if executable_path:
        if os.path.exists(executable_path):
            final_executable_path = executable_path
        else:
            logger.warning(f"Executable path provided in CLI does not exist: {executable_path}")

    # 2. Check Config if CLI is not set or invalid
    if not final_executable_path:
        config_path = config.get("executable_path")
        if config_path:
            if os.path.exists(config_path):
                final_executable_path = config_path
            else:
                logger.warning(f"Executable path in config does not exist: {config_path}")

    # 3. Check System Default
    if not final_executable_path:
        if sys.platform == "win32":
            # Common Windows paths for Chrome
            possible_paths = [
                os.path.join(
                    os.environ.get("ProgramFiles", "C:\\Program Files"),
                    "Google\\Chrome\\Application\\chrome.exe",
                ),
                os.path.join(
                    os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
                    "Google\\Chrome\\Application\\chrome.exe",
                ),
                os.path.join(
                    os.environ.get("LocalAppData", os.path.expanduser("~\\AppData\\Local")),
                    "Google\\Chrome\\Application\\chrome.exe",
                ),
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    final_executable_path = p
                    break
        elif sys.platform == "darwin":
            p = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if os.path.exists(p):
                final_executable_path = p
        else:
            # Linux default
            p = "/opt/google/chrome/chrome"
            if os.path.exists(p):
                final_executable_path = p

    if not final_executable_path:
        # Construct helpful error message based on platform
        if sys.platform == "win32":
            suggested_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        elif sys.platform == "darwin":
            suggested_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        else:
            suggested_path = "/opt/google/chrome/chrome"

        error_msg = (
            f"No valid browser executable found.\n"
            f"Please ensure Chrome is installed at {suggested_path}, "
            f"or provide a valid --executable-path in CLI, "
            f"or set a valid 'executable_path' in {mcp_config_path}."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.info(f"Using browser executable at: {final_executable_path}")

    # Override other parameters from config if available
    width = config.get("width", width)
    height = config.get("height", height)
    isolated = config.get("isolated", isolated)

    client_args = ["@playwright/mcp@latest"]
    
    # Viewport size
    client_args.append(f"--viewport-size={width}x{height}")
    
    # Isolation
    if isolated:
        client_args.append("--isolated")
    
    # CDP Endpoint
    if cdp_endpoint:
        client_args.append("--cdp-endpoint")
        client_args.append(cdp_endpoint)
    
    # Executable path
    client_args.append("--executable-path")
    client_args.append(final_executable_path)
        
    # Recording
    if video_manager:
        # If record_session is True or agent clips are expected, we enable recording
        # For simplicity, if a VideoManager is passed, we assume recording is desired
        video_manager.enable_mcp_recording()
        client_args.append(f"--save-video={width}x{height}")
        client_args.append(f"--output-dir={video_manager.get_output_dir()}")
        
    env = os.environ.copy()
    
    if headless:
        client_args.append("--headless")
        # Ensure env var is consistent if user wants headless
        env["PLAYWRIGHT_MCP_HEADLESS"] = "true"
    else:
        # User wants headed (default). 
        # Removing it ensures it doesn't force headless if set elsewhere.
        if "PLAYWRIGHT_MCP_HEADLESS" in env:
            del env["PLAYWRIGHT_MCP_HEADLESS"]

    # On Windows, npx might need to be npx.cmd for subprocess to find it
    command = "npx"
    if sys.platform == "win32" and shutil.which("npx.cmd"):
        command = "npx.cmd"

    return StdIOStatefulClient(
        name="playwright-mcp",
        command=command,
        args=client_args,
        env=env,
    ), final_executable_path
