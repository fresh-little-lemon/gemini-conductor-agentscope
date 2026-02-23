# -*- coding: utf-8 -*-
"""Video recording manager for browser agent."""
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict

class VideoManager:
    """
    Manages global session recording and semantic clip extraction.
    Designed to be used by one or more agents.
    """
    
    def __init__(self, session_dir: str | Path, record_session: bool = False):
        self.session_dir = Path(session_dir)
        self.record_session = record_session # Whether to keep the full replay.mp4
        
        self.video_root = self.session_dir / "videos"
        self.tmp_dir = self.video_root / "tmp"
        self.final_output = self.video_root / "replay.mp4"
        self.clips_dir = self.video_root / "clips"
        
        # Timeline for clips: {label: {"start": float, "end": float}}
        self.clip_marks: Dict[str, Dict[str, float]] = {}
        self.session_start_time: Optional[float] = None
        
        # We enable the underlying recording if the user wants a full record
        # OR if we want to allow agents to extract clips.
        # For now, we assume if VideoManager exists, we allow agent clips if MCP is recording.
        self.mcp_recording_enabled = False 

    def enable_mcp_recording(self):
        """Signals that the underlying MCP server should record."""
        self.mcp_recording_enabled = True
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def start_session(self):
        """Marks the absolute start time of the browser session."""
        self.session_start_time = time.time()

    def get_output_dir(self) -> Optional[str]:
        """Returns the temporary directory path for MCP."""
        return str(self.tmp_dir) if self.mcp_recording_enabled else None

    def start_clip(self, label: str, category: str = "task"):
        """Marks the start of a semantic clip with a category."""
        if not self.mcp_recording_enabled:
            raise RuntimeError("Recording was not enabled for this browser instance.")
        if self.session_start_time is None:
            self.start_session()
            
        offset = time.time() - self.session_start_time
        self.clip_marks[label] = {
            "start": max(0, offset - 0.5),
            "category": category
        }

    def stop_clip(self, label: str):
        """Marks the end of a semantic clip."""
        if label not in self.clip_marks:
            return
        offset = time.time() - self.session_start_time
        self.clip_marks[label]["end"] = offset + 0.5

    def finalize(self) -> None:
        """Processes the session video: creates replay and/or clips."""
        if not self.mcp_recording_enabled or not self.tmp_dir.exists():
            return
            
        try:
            time.sleep(1) # FS sync
            webm_files = list(self.tmp_dir.glob("**/*.webm"))
            if not webm_files:
                return
                
            latest_video = max(webm_files, key=os.path.getmtime)
            
            if not shutil.which("ffmpeg"):
                # Fallback: if no ffmpeg, we can't clip, just move the whole thing if requested
                if self.record_session:
                    shutil.copy2(latest_video, self.final_output.with_suffix(".webm"))
                shutil.rmtree(self.tmp_dir)
                return

            # 1. Determine if we need to process the full video
            source_for_clips = latest_video
            
            if self.record_session or self.clip_marks:
                # Convert to MP4 once as source
                temp_mp4 = self.tmp_dir / "full_session_temp.mp4"
                subprocess.run([
                    "ffmpeg", "-y", "-i", str(latest_video),
                    "-c:v", "libx264", "-crf", "23", "-pix_fmt", "yuv420p",
                    "-loglevel", "error", str(temp_mp4)
                ], check=True)
                
                if self.record_session:
                    self.video_root.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(temp_mp4), str(self.final_output))
                    source_for_clips = self.final_output
                    print(f"Global replay saved to: {self.final_output}")
                else:
                    source_for_clips = temp_mp4

            # 2. Extract Semantic Clips (only if marks exist)
            if self.clip_marks:
                self.clips_dir.mkdir(parents=True, exist_ok=True)
                for label, info in self.clip_marks.items():
                    times = info
                    end_time = times.get("end", time.time() - self.session_start_time)
                    duration = end_time - times["start"]
                    
                    if duration <= 0: continue
                    
                    # Distinguish subfolders based on category
                    category = times.get("category", "task")
                    target_dir = self.clips_dir / category
                    target_dir.mkdir(parents=True, exist_ok=True)
                    
                    clip_path = target_dir / f"{label}.mp4"
                    subprocess.run([
                        "ffmpeg", "-y", "-ss", f"{times['start']:.3f}", 
                        "-t", f"{duration:.3f}", "-i", str(source_for_clips), 
                        "-c", "copy", "-loglevel", "error", str(clip_path)
                    ], check=True)
                    print(f"[{category.upper()}] Clip '{label}' saved to: {clip_path}")

            # Cleanup
            shutil.rmtree(self.tmp_dir)
            
            # Remove videos dir if empty (e.g. no clips and no session record)
            if self.video_root.exists() and not any(self.video_root.iterdir()):
                self.video_root.rmdir()
                
        except Exception as e:
            print(f"Error in video finalization: {e}")
