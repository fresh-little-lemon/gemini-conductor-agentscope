# -*- coding: utf-8 -*-
"""Standalone video understanding skill for the browser agent."""
# flake8: noqa: E501
# pylint: disable=W0212
# pylint: disable=too-many-lines
# pylint: disable=C0301
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import uuid
from base64 import b64encode
from pathlib import Path
from typing import Any, List, Optional

from agentscope.message import (
    Base64Source,
    ImageBlock,
    Msg,
    TextBlock,
)
from agentscope.tool import ToolResponse


async def video_understanding(
    browser_agent: Any,
    video_path: str,
    task: str,
) -> ToolResponse:
    """
    Perform video understanding on the provided video file or recording label.

    Args:
        video_path (str): The path or label of the video file to analyze.
        If a label was used in `browser_start_recording`, use that label.
        If no path is found, the tool will attempt to use the current
        active recording.
        task (str): The specific task or question to solve about
        the video (e.g., summary, object detection, activity recognition,
        or answering a question about the video's content).

    Returns:
        ToolResponse: A structured response containing the answer
        to the specified task based on the video content.
    """

    workdir = _prepare_workdir(browser_agent)
    resolved_source, start_time, duration = _resolve_video_info(browser_agent, video_path)
    
    if not resolved_source or not os.path.exists(resolved_source):
        return _error_response(
            f"Video source not found for: '{video_path}'. \n"
            "If you intended to analyze a live animation, you MUST first "
            "start recording using `browser_start_recording`, wait for the "
            "animation to play, and then call `browser_stop_recording`. \n"
            "Note: `browser_snapshot` creates a text-based accessibility tree, "
            "NOT a video file."
        )

    # 1. Copy source to workdir to avoid locking/growth issues during conversion
    source_ext = os.path.splitext(resolved_source)[1] or ".webm"
    local_source_path = os.path.join(workdir, f"source_snapshot{source_ext}")
    try:
        import shutil
        # Wait a bit longer to allow browser buffers to flush to disk
        # and ensure Matroska clusters are well-formed.
        import time
        time.sleep(1.0)
        shutil.copy2(resolved_source, local_source_path)
    except Exception as exc:
        return _error_response(f"Failed to snapshot live recording: {exc}")

    # 2. Prepare the segment for analysis (Convert to MP4 for compatibility)
    local_video_path = os.path.join(workdir, "segment_to_analyze.mp4")
    try:
            # Use flags to ignore premature EOF and other Matroska inconsistencies 
            # common in live recordings.
            common_input_flags = [
                "-probesize", "10M",
                "-analyzeduration", "10M",
                "-err_detect", "ignore_err",
                "-ignore_unknown",
            ]
            
            # Use subprocess.DEVNULL to suppress "File ended prematurely" noise 
            # while the command still succeeds.
            run_kwargs = {
                "check": True,
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
            }
            
            if start_time is not None:
                # Extract segment from the local source snapshot
                cmd = ["ffmpeg", "-y"] + common_input_flags
                cmd.extend(["-ss", f"{start_time:.3f}", "-i", local_source_path])
                
                if duration > 0:
                    cmd.extend(["-t", f"{duration:.3f}"])
                
                # Use H.264 in MP4 container - widely supported
                cmd.extend([
                    "-c:v", "libx264", "-crf", "23", "-pix_fmt", "yuv420p",
                    "-preset", "veryfast", # Speed up mid-task processing
                    local_video_path
                ])
                subprocess.run(cmd, **run_kwargs)
            else:
                # Full source conversion
                cmd = ["ffmpeg", "-y"] + common_input_flags + ["-i", local_source_path]
                cmd.extend([
                    "-c:v", "libx264", "-crf", "23", "-pix_fmt", "yuv420p",
                    "-preset", "veryfast",
                    local_video_path
                ])
                subprocess.run(cmd, **run_kwargs)
    except Exception as exc:
        return _error_response(
            f"Failed to process video segment. "
            f"This often happens if the recording is extremely short or the file structure is not yet finalized by the browser. "
            f"Try waiting a few seconds before calling this tool. \n"
            f"Error Details: {exc}"
        )

    if not _is_video_file(local_video_path):
        return _error_response(
            f"The resolved source '{resolved_source}' could not be processed into a valid video."
        )

    try:
        frames_dir = os.path.join(workdir, "frames")
        frames = extract_frames(local_video_path, frames_dir)
    except Exception as exc:
        return _error_response(f"Failed to extract frames: {exc}")

    audio_path = os.path.join(
        workdir,
        f"audio_{getattr(browser_agent, 'iter_n', 0)}.wav",
    )
    try:
        # We try to extract audio, but don't fail if it doesn't have an audio track
        extract_audio(local_video_path, audio_path)
        transcript = audio2text(audio_path)
    except Exception:
        transcript = "[No audio track or transcription failed]"

    sys_prompt = (
        "You are a web video analysis expert. "
        "Given the following video frames and audio transcript, "
        "analyze the content and provide a solution to the task. "
        'Return ONLY a JSON object: {"answer": <your answer>}'
    )

    content_blocks = _build_multimodal_blocks(frames, transcript, task)

    prompt = await browser_agent.formatter.format(
        msgs=[
            Msg("system", sys_prompt, role="system"),
            Msg("user", content_blocks, role="user"),
        ],
    )

    res = await browser_agent.model(prompt)
    model_text = ""
    if browser_agent.model.stream:
        async for chunk in res:
            if chunk.content:
                for block in chunk.content:
                    if block["type"] == "text":
                        model_text += block.get("text", "")
    else:
        for block in res.content:
            if block["type"] == "text":
                model_text += block.get("text", "")

    try:
        # Robust JSON extraction
        json_pattern = r"\{.*\}"
        match = re.search(json_pattern, model_text, re.DOTALL)
        if match:
            json_str = match.group()
            answer_info = json.loads(json_str)
        else:
            answer_info = json.loads(model_text)
            
        answer = answer_info.get("answer", "")
    except Exception:  # pylint: disable=broad-except
        return _error_response(
            f"Failed to parse answer from model output. Raw output: {model_text}"
        )

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=(
                    "Video analysis completed.\n" f"Task solution: {answer}"
                ),
            ),
        ],
    )


def _resolve_video_info(
    browser_agent: Any, 
    video_path: str
) -> tuple[Optional[str], Optional[float], float]:
    """
    Resolves video source and timing information.
    Returns (path, start_offset, duration)
    """
    video_manager = getattr(browser_agent, "video_manager", None)
    
    # 1. Check if it's a known label in VideoManager
    if video_manager and video_path in video_manager.clip_marks:
        marks = video_manager.clip_marks[video_path]
        import time
        start = marks["start"]
        # If stop_clip wasn't called yet, use current time
        end = marks.get("end", time.time() - video_manager.session_start_time)
        duration = end - start
        
        # Source is the active recording in tmp_dir
        try:
            webm_files = list(video_manager.tmp_dir.glob("**/*.webm"))
            if webm_files:
                latest_video = max(webm_files, key=os.path.getmtime)
                return str(latest_video), start, duration
        except Exception:
            pass

    # 2. Check if it's a direct file path
    if os.path.exists(video_path) and os.path.isfile(video_path):
        return video_path, None, 0.0

    if not video_manager:
        return None, None, 0.0

    # 3. Try clips directory (finalized clips from previous sessions or manual)
    possible_paths = [
        video_manager.clips_dir / video_path,
        video_manager.clips_dir / f"{video_path}.mp4",
        video_manager.video_root / video_path,
        video_manager.video_root / f"{video_path}.mp4",
    ]
    for path in possible_paths:
        if path.exists():
            return str(path), None, 0.0

    # 4. Fallback: use the latest .webm recording as a whole
    try:
        webm_files = list(video_manager.tmp_dir.glob("**/*.webm"))
        if webm_files:
            latest_video = max(webm_files, key=os.path.getmtime)
            return str(latest_video), None, 0.0
    except Exception:
        pass

    return None, None, 0.0


def _is_video_file(file_path: str) -> bool:
    """Basic check if the file is a likely video file."""
    if not os.path.exists(file_path): return False
    
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".mp4", ".webm", ".mkv", ".avi", ".mov"]:
        return True
    
    # Use ffprobe for a deeper check
    try:
        command = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=codec_type", "-of", "csv=p=0",
            file_path
        ]
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, timeout=5
        )
        return "video" in result.stdout
    except Exception:
        return False




def audio2text(audio_path: str) -> str:
    """Convert audio to text using DashScope ASR."""

    try:  # Local import to avoid hard dependency when unused.
        from dashscope.audio.asr import Recognition, RecognitionCallback
    except ImportError as exc:
        raise RuntimeError(
            "dashscope.audio is required for audio transcription.",
        ) from exc

    callback = RecognitionCallback()
    recognizer = Recognition(
        model="paraformer-realtime-v1",
        format="wav",
        sample_rate=16000,
        callback=callback,
    )

    result = recognizer.call(audio_path)
    sentences = result.get("output", {}).get("sentence", [])
    return " ".join(sentence.get("text", "") for sentence in sentences)


def extract_frames(
    video_path: str,
    output_dir: str,
    max_frames: int = 16,
) -> List[str]:
    """Extract representative frames using ffmpeg (no OpenCV dependency)."""

    if max_frames <= 0:
        raise ValueError("max_frames must be greater than zero.")

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video path not found: {video_path}")

    os.makedirs(output_dir, exist_ok=True)

    # Clean up previous generated frames
    for existing in Path(output_dir).glob("frame_*.jpg"):
        try:
            existing.unlink()
        except OSError:
            # Ignore errors during cleanup;
            # leftover files will be overwritten or do not affect frame extraction
            pass

    duration = _probe_video_duration(video_path)
    if duration and duration > 0:
        fps = max_frames / duration
    else:
        fps = 1.0

    fps = max(min(fps, 30.0), 0.1)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vf",
        f"fps={fps:.5f}",
        "-frames:v",
        str(max_frames),
        os.path.join(output_dir, "frame_%04d.jpg"),
    ]

    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "ffmpeg is required to extract frames from video.",
        ) from exc

    frame_files = sorted(
        str(path) for path in Path(output_dir).glob("frame_*.jpg")
    )

    if not frame_files:
        raise RuntimeError("No frames could be extracted from the video.")

    return frame_files


def extract_audio(video_path: str, audio_path: str) -> str:
    """Extract audio track with ffmpeg and save as wav."""

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video path not found: {video_path}")

    os.makedirs(os.path.dirname(audio_path), exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        audio_path,
    ]

    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "ffmpeg is required to extract audio from video.",
        ) from exc

    return audio_path


def _probe_video_duration(video_path: str) -> Optional[float]:
    """Return the video duration in seconds using ffprobe, if available."""

    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]

    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        duration_str = result.stdout.strip()
        if duration_str:
            return float(duration_str)
    except (FileNotFoundError, ValueError, subprocess.CalledProcessError):
        return None

    return None


def _build_multimodal_blocks(
    frames: List[str],
    transcript: str,
    task: str,
) -> list:
    """Construct multimodal content blocks for the model input."""

    blocks: list = []
    for frame_path in frames:
        with open(frame_path, "rb") as file:
            data = b64encode(file.read()).decode("ascii")
        image_block = ImageBlock(
            type="image",
            source=Base64Source(
                type="base64",
                media_type="image/jpeg",
                data=data,
            ),
        )
        blocks.append(image_block)

    blocks.append(
        TextBlock(
            type="text",
            text=f"Audio transcript:\n{transcript}",
        ),
    )
    blocks.append(
        TextBlock(
            type="text",
            text=f"The task to be solved is: {task}",
        ),
    )
    return blocks


def _prepare_workdir(browser_agent: Any) -> str:
    """Prepare a working directory for intermediate artifacts."""

    base_dir = getattr(browser_agent, "state_saving_dir", None)
    if not base_dir:
        base_dir = tempfile.gettempdir()

    workdir = os.path.join(base_dir, "video_understanding", uuid.uuid4().hex)
    os.makedirs(workdir, exist_ok=True)
    return workdir


def _error_response(message: str) -> ToolResponse:
    """Create a standardized error response."""

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=message,
            ),
        ],
        metadata={"success": False},
    )
