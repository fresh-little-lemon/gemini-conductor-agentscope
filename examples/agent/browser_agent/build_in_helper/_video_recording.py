# -*- coding: utf-8 -*-
"""Standalone video recording tool for the browser agent."""
# flake8: noqa: E501
# pylint: disable=W0212,W0107,C0301

from __future__ import annotations
from typing import Any, Literal

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse


async def browser_start_recording(
    browser_agent: Any,
    label: str = "task_segment",
    mode: str = "task"
) -> ToolResponse:
    """
    Start recording a specific task or action segment.
    
    Args:
        label (str): A meaningful name for this recording clip.
        mode (str): The purpose of the recording. 
            - 'task': For recordings explicitly requested by the user.
            - 'observation': For internal agent use (e.g., to feed into video_understanding).
    
    Returns:
        ToolResponse: Confirmation message.
    """
    video_manager = getattr(browser_agent, "video_manager", None)
    
    if not video_manager or not video_manager.mcp_recording_enabled:
        return ToolResponse(
            content=[TextBlock(type="text", text="Video recording engine is not enabled. Agent recording tools are unavailable.")],
            metadata={"success": False}
        )
    
    # Check if this label is already active to prevent loops
    if label in video_manager.clip_marks and "end" not in video_manager.clip_marks[label]:
        return ToolResponse(
            content=[TextBlock(type="text", text=f"Recording for '{label}' is ALREADY ACTIVE and running. Do NOT call `browser_start_recording` again for this label. Proceed to your next action or subtask.")],
            metadata={"success": True, "label": label, "already_active": True}
        )
        
    try:
        video_manager.start_clip(label, category=mode)
        return ToolResponse(
            content=[TextBlock(type="text", text=f"Started {mode} recording: '{label}'. Remember to stop when finished. This label is now active.")],
            metadata={"success": True, "label": label, "mode": mode}
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
    
    if label not in video_manager.clip_marks:
        return ToolResponse(
            content=[TextBlock(type="text", text=f"No active recording found with label '{label}'. Check your labels or start a new recording.")],
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
