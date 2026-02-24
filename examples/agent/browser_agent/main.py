# -*- coding: utf-8 -*-
# pylint: disable=too-many-lines
"""The main entry point of the browser agent example."""
import argparse
import asyncio
import os
import sys
import traceback

from pydantic import BaseModel, Field

from agentscope.agent import UserAgent
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg
from agentscope.tool import Toolkit
from browser_agent import BrowserAgent
from utils.logger_utils import setup_session_logger
from utils.mcp_utils import create_browser_client
from utils.model_loader import AutoFormatter, AutoModel
from utils.token_tracker import TokenUsageTracker
from utils.url_utils import LocalFileServer, sanitize_start_url
from utils.video_manager import VideoManager


class FinalResult(BaseModel):
    """A structured result model for structured output."""

    result: str = Field(
        description="The final result to the initial user query",
    )


async def main(
    start_url_param: str = "https://www.google.com",
    max_iters_param: int = 50,
    model_config: str = "configs/model_config.json",
    args_dict: dict | None = None,
    headless: bool = False,
    record_video: bool = False,
    executable_path: str | None = None,
    mcp_config: str = "configs/mcp_config.json",
    prompt: str | None = None,
) -> None:
    """The main entry point for the browser agent example."""
    # Initialize token usage tracker early to get session directory
    tracker = TokenUsageTracker()
    session_dir = tracker.session_dir

    # Initialize video manager with full session record flag
    # Capability is always enabled for agent clips
    video_manager = VideoManager(session_dir, record_session=record_video)

    # Initialize local server if needed
    local_server = None
    if start_url_param.startswith("file://"):
        local_server = LocalFileServer(start_url_param)
        start_url_param = local_server.hosted_url

    # Setup toolkit with browser tools from MCP server
    toolkit = Toolkit()
    
    # Always pass the video manager to enable recording at MCP level
    # so that agent tools work out of the box.
    browser_client, final_executable_path = create_browser_client(
        headless=headless,
        video_manager=video_manager,
        isolated=True, # Default to isolated as per requirements
        executable_path=executable_path,
        mcp_config_path=mcp_config,
    )

    try:
        # Connect to the browser client
        await browser_client.connect()
        await toolkit.register_mcp_client(browser_client)

        # Mark session start for video manager timeline
        video_manager.start_session()

        # Update args_dict with the actual executable path for logging
        if args_dict:
            args_dict["executable_path"] = final_executable_path
            
        # Setup session logging
        session_logger = setup_session_logger(session_dir, tracker.timestamp, args_dict or {})

        # Load model and formatter from config
        model = AutoModel.from_config(model_config)
        # Track model usage
        model = tracker.track_model(model)

        formatter = AutoFormatter.from_config(model_config)

        # Track toolkit calls
        toolkit = tracker.track_toolkit(toolkit)

        agent = BrowserAgent(
            name="Browser-Use Agent",
            model=model,
            formatter=formatter,
            memory=InMemoryMemory(),
            toolkit=toolkit,
            max_iters=max_iters_param,
            start_url=start_url_param,
            token_counter=tracker,
        )
        
        # Attach video manager to agent for tool usage
        agent.video_manager = video_manager

        # Register agent hooks for active time tracking
        agent_hooks = tracker.get_agent_hooks()
        agent.register_instance_hook(
            "pre_reply",
            "tracker_pre_reply",
            agent_hooks["pre_reply"],
        )
        agent.register_instance_hook(
            "post_reply",
            "tracker_post_reply",
            agent_hooks["post_reply"],
        )

        if prompt:
            # Non-interactive mode: execute provided prompt and exit
            msg = Msg("User", prompt, role="user")
            await agent(msg, structured_model=FinalResult)
        else:
            # Interactive mode: loop until 'exit'
            user = UserAgent("User")
            msg = None
            while True:
                msg = await user(msg)
                if msg.get_text_content() == "exit":
                    break
                msg = await agent(msg, structured_model=FinalResult)
                await agent.memory.clear()

        # Update session log with token usage summary
        session_logger.set_summary(tracker.get_summary_dict())

        # Show usage summary
        tracker.show_summary()

    except asyncio.CancelledError:
        # This is typically raised when Ctrl+C is pressed
        print("Main task cancelled (Ctrl+C). Initiating graceful shutdown...")
        # Re-raise to ensure asyncio.run knows about the cancellation and terminates properly
        raise
    except Exception as e:
        traceback.print_exc()
        print(f"An error occurred: {e}")
        print("Cleaning up browser client...")
    finally:
        # Use a more task-stable pattern for cleanup to avoid anyio context warnings
        async def perform_cleanup():
            try:
                if browser_client:
                    # Explicitly call browser_close tool to release resources
                    try:
                        print("Requesting browser to close...")
                        await asyncio.wait_for(
                            browser_client.call_tool("browser_close", {}),
                            timeout=3.0
                        )
                    except Exception:
                        # Tool might not be available or connection already lost
                        pass

                    await browser_client.close()
                    print("Browser client closed successfully.")
                
                # Finalize video processing
                if 'video_manager' in locals():
                    video_manager.finalize()

                # Shutdown local server if running
                if 'local_server' in locals() and local_server:
                    local_server.stop()
            except Exception as cleanup_error:
                print(f"Error during cleanup execution: {cleanup_error}")

        # Create a task and wait for it to finish, ignoring further cancellations
        cleanup_task = asyncio.create_task(perform_cleanup())
        while not cleanup_task.done():
            try:
                await asyncio.wait([cleanup_task])
            except asyncio.CancelledError:
                # Keep waiting until the cleanup task is truly finished
                pass


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Browser Agent Example with configurable reply method",
    )
    parser.add_argument(
        "--start-url",
        type=str,
        default="https://www.google.com",
        help=(
            "Starting URL for the browser agent "
            "(default: https://www.google.com)"
        ),
    )
    parser.add_argument(
        "--max-iters",
        type=int,
        default=50,
        help="Maximum number of iterations (default: 50)",
    )
    parser.add_argument(
        "--model-config",
        type=str,
        default="configs/model_config.json",
        help="Path to the model configuration file (default: configs/model_config.json)",
    )
    parser.add_argument(
        "--mcp-config",
        type=str,
        default="configs/mcp_config.json",
        help="Path to the MCP configuration file (default: configs/mcp_config.json)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (default: False, i.e., headed)",
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="Record full session video (saved to session_logs/)",
    )
    parser.add_argument(
        "--executable-path",
        type=str,
        help="Path to the browser executable",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Enable local mode to load local HTML files",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        help="Run in non-interactive mode with the given prompt and exit",
    )
    return parser.parse_args()


if __name__ == "__main__":
    print("Starting Browser Agent Example...")
    print(
        "The browser agent will use "
        "playwright-mcp (https://github.com/microsoft/playwright-mcp)."
        "Make sure the MCP server is installed "
        "by `npx @playwright/mcp@latest`",
    )
    print("\nUsage examples:")
    print("  python main.py                           # Start with defaults (headed)")
    print("  python main.py --headless                # Start in headless mode")
    print("  python main.py --record                 # Record full session video")
    print("  python main.py --prompt \"YOUR_PROMPT\"    # Run once and exit")
    print("  python main.py --executable-path /path/to/chrome")
    print("  python main.py --start-url https://example.com --max-iters 100")
    print("  python main.py --start-url /path/to/local.html --local")
    print("  python main.py --model-config configs/my_config.json")
    print("  python main.py --help                   # Show all options")
    print()

    # Parse command line arguments
    args = parse_arguments()

    # Get other parameters
    start_url = args.start_url
    max_iters = args.max_iters
    model_config = args.model_config
    mcp_config = args.mcp_config
    headless_mode = args.headless
    record_session = args.record
    executable_path = args.executable_path
    prompt = args.prompt
    local_mode = args.local

    # Validate parameters
    if max_iters <= 0:
        print("Error: max-iters must be positive")
        sys.exit(1)

    # Process start-url
    try:
        start_url, local_mode = sanitize_start_url(start_url)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Update args for consistent logging
    args.start_url = start_url
    args.local = local_mode

    if not os.path.exists(model_config):
        print(f"Error: Model config file not found: {model_config}")
        sys.exit(1)

    print(f"Starting URL: {start_url}")
    if local_mode:
        print("Local mode: Enabled")
    print(f"Maximum iterations: {max_iters}")
    print(f"Model config: {model_config}")
    if os.path.exists(mcp_config):
        print(f"MCP config: {mcp_config}")
    else:
        # For logging, set to null if not exists
        args.mcp_config = None
        
    print(f"Headless mode: {headless_mode}")
    print(f"Record session: {record_session}")
    if executable_path:
        print(f"Executable path: {executable_path}")
    if prompt:
        print(f"Prompt: {prompt} (Non-interactive mode)")
    print()

    asyncio.run(
        main(
            start_url,
            max_iters,
            model_config,
            vars(args),
            headless=headless_mode,
            record_video=record_session,
            executable_path=executable_path,
            mcp_config=mcp_config,
            prompt=prompt,
        ),
    )
