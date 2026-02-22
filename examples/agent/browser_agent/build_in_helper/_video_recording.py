# -*- coding: utf-8 -*-
"""Standalone video recording tool for the browser agent."""
# flake8: noqa: E501
# pylint: disable=W0212,W0107,C0301

from __future__ import annotations
from typing import Any

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse


async def browser_start_recording(
    browser_agent: Any,
    label: str = "task_segment"
) -> ToolResponse:
    """
    Start recording a specific task or action segment.
    
    Args:
        label (str): A meaningful name for this recording clip (e.g., 'user_login', 'checkout_process').
    
    Returns:
        ToolResponse: Confirmation message.
    """
    video_manager = getattr(browser_agent, "video_manager", None)
    
    if not video_manager or not video_manager.mcp_recording_enabled:
        return ToolResponse(
            content=[TextBlock(type="text", text="Video recording engine is not enabled. Agent recording tools are unavailable.")],
            metadata={"success": False}
        )
        
    try:
        video_manager.start_clip(label)
        return ToolResponse(
            content=[TextBlock(type="text", text=f"Started recording clip: '{label}'. Remember to stop recording when finished.")],
            metadata={"success": True, "label": label}
        )
    except Exception as e:
        return ToolResponse(
            content=[TextBlock(type="text", text=f"Failed to start recording: {e}")],
            metadata={"success": False}
        )


async def browser_stop_recording(
    browser_agent: Any,
    label: str = "task_segment"
) -> ToolResponse:
    """
    Stop recording the current task or action segment.
    
    Args:
        label (str): The label provided when starting the recording.
    
    Returns:
        ToolResponse: Confirmation message.
    """
    video_manager = getattr(browser_agent, "video_manager", None)
    
    if not video_manager or not video_manager.mcp_recording_enabled:
        return ToolResponse(
            content=[TextBlock(type="text", text="Video recording engine is not enabled.")],
            metadata={"success": False}
        )
        
    try:
        video_manager.stop_clip(label)
        return ToolResponse(
            content=[TextBlock(type="text", text=f"Finished recording clip: '{label}'. The clip will be finalized after session ends.")],
            metadata={"success": True, "label": label}
        )
    except Exception as e:
        return ToolResponse(
            content=[TextBlock(type="text", text=f"Failed to stop recording: {e}")],
            metadata={"success": False}
        )
