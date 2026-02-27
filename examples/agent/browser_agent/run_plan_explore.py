# -*- coding: utf-8 -*-
"""Entry point for the Plan + Explore pipeline.

Usage:
    python run_plan_explore.py --html-path html_0210/100.html
    python run_plan_explore.py --html-path html_0210/100.html --headless --record
    python run_plan_explore.py --html-path html_0210/ --max-concurrent 2
"""
# pylint: disable=C0301

import argparse
import asyncio
import os
import sys
import traceback

from orchestrator import Orchestrator


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Plan + Explore Pipeline: Analyze HTML source code and "
        "execute interactive exploration with parallel browser agents.",
    )
    parser.add_argument(
        "--html-path",
        type=str,
        required=True,
        help="Path to HTML file or directory of HTML files to analyze.",
    )
    parser.add_argument(
        "--model-config",
        type=str,
        default="configs/model_config.json",
        help="Path to model configuration file (default: configs/model_config.json)",
    )
    parser.add_argument(
        "--mcp-config",
        type=str,
        default="configs/mcp_config.json",
        help="Path to MCP configuration file (default: configs/mcp_config.json)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browsers in headless mode (default: False)",
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="Record video for each subagent session",
    )
    parser.add_argument(
        "--executable-path",
        type=str,
        help="Path to the browser executable",
    )
    parser.add_argument(
        "--max-iters",
        type=int,
        default=30,
        help="Maximum iterations per subagent (default: 30)",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=3,
        help="Maximum number of concurrent subagents (default: 3)",
    )
    return parser.parse_args()


async def main() -> None:
    """Main async entry point."""
    args = parse_arguments()

    # Validate html-path
    if not os.path.exists(args.html_path):
        print(f"Error: HTML path not found: {args.html_path}")
        sys.exit(1)

    # Validate model config
    if not os.path.exists(args.model_config):
        print(f"Error: Model config not found: {args.model_config}")
        sys.exit(1)

    # Print configuration
    print("=" * 60)
    print("Plan + Explore Pipeline")
    print("=" * 60)
    print(f"  HTML Path:       {args.html_path}")
    print(f"  Model Config:    {args.model_config}")
    print(f"  MCP Config:      {args.mcp_config}")
    print(f"  Headless:        {args.headless}")
    print(f"  Record Video:    {args.record}")
    print(f"  Max Iterations:  {args.max_iters}")
    print(f"  Max Concurrent:  {args.max_concurrent}")
    if args.executable_path:
        print(f"  Executable:      {args.executable_path}")
    print("=" * 60)
    print()

    # Create orchestrator
    orchestrator = Orchestrator(
        model_config=args.model_config,
        mcp_config=args.mcp_config,
        headless=args.headless,
        record_video=args.record,
        executable_path=args.executable_path,
        max_iters=args.max_iters,
        max_concurrent=args.max_concurrent,
    )

    # Handle single file or directory
    if os.path.isfile(args.html_path):
        html_files = [args.html_path]
    elif os.path.isdir(args.html_path):
        html_files = sorted([
            os.path.join(args.html_path, f)
            for f in os.listdir(args.html_path)
            if f.endswith((".html", ".htm"))
        ])
        if not html_files:
            print(f"Error: No HTML files found in {args.html_path}")
            sys.exit(1)
        print(f"Found {len(html_files)} HTML file(s) to process.")
        print()
    else:
        print(f"Error: {args.html_path} is neither a file nor a directory")
        sys.exit(1)

    # Process each HTML file
    for i, html_file in enumerate(html_files):
        print(f"\n{'='*60}")
        print(f"Processing [{i+1}/{len(html_files)}]: {html_file}")
        print(f"{'='*60}\n")

        try:
            result = await orchestrator.run(html_file)
            print(f"\n✅ Completed: {html_file}")
            print(f"   Session:  {result['session_dir']}")
            print(f"   Report:   {result['report_path']}")
        except Exception as e:
            print(f"\n❌ Failed: {html_file}")
            print(f"   Error: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    print("Starting Plan + Explore Pipeline...")
    print(
        "This pipeline will analyze HTML source code and execute "
        "interactive exploration with parallel browser agents."
    )
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user.")
    except Exception as e:
        print(f"\nFatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
