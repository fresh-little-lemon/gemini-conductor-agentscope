# -*- coding: utf-8 -*-
"""MCP Utility for browser agent."""
import os
import json
import sys
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
    mcp_config_path: str = "configs/mcp_config.json"
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
    # 2. System Default (if exists)
    # 3. Config path (if exists)
    default_system_path = "/opt/google/chrome/chrome"
    
    final_executable_path = None
    
    # Check CLI path first
    if executable_path:
        if os.path.exists(executable_path):
            final_executable_path = executable_path
        else:
            logger.warning(f"Executable path provided in CLI does not exist: {executable_path}")
            logger.warning(f"Falling back to check system default...")

    # Check System Default if CLI is not set or invalid
    if not final_executable_path:
        if os.path.exists(default_system_path):
            final_executable_path = default_system_path
        else:
            # Check Config if System Default is not available
            config_path = config.get("executable_path")
            if config_path:
                if os.path.exists(config_path):
                    final_executable_path = config_path
                else:
                    logger.warning(f"Executable path in config does not exist: {config_path}")

    if not final_executable_path:
        error_msg = (
            f"No valid browser executable found.\n"
            f"Please ensure Chrome is installed at {default_system_path}, "
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

    return StdIOStatefulClient(
        name="playwright-mcp",
        command="npx",
        args=client_args,
        env=env,
    ), final_executable_path
