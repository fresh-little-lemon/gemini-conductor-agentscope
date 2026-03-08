import os
import json
from typing import List, Dict, Any
from pydantic import BaseModel

class SessionSummary(BaseModel):
    id: str
    timestamp: str
    title: str
    status: str
    task_count: int

class SessionIndexer:
    def __init__(self, sessions_dir: str) -> None:
        self.sessions_dir = sessions_dir

    def list_sessions(self) -> List[SessionSummary]:
        summaries = []
        if not os.path.exists(self.sessions_dir):
            return []
            
        for session_id in os.listdir(self.sessions_dir):
            path = os.path.join(self.sessions_dir, session_id)
            if os.path.isdir(path):
                summary = self._parse_session(session_id, path)
                if summary:
                    summaries.append(summary)
        
        # Sort by timestamp descending
        summaries.sort(key=lambda x: x.timestamp, reverse=True)
        return summaries

    def _parse_session(self, session_id: str, path: str) -> SessionSummary | None:
        # Try to read results.json for metadata
        results_path = os.path.join(path, "results.json")
        try:
            timestamp = session_id # Fallback if we can't find a better one
            title = "Untitled Session"
            status = "unknown"
            task_count = 0
            
            if os.path.exists(results_path):
                with open(results_path, "r", encoding="utf-8") as f:
                    results = json.load(f)
                    task_count = len(results)
                    # We could infer more here
            
            # Extract timestamp from folder name if it matches the pattern YYYY-MM-DD_HH-MM-SS
            # Agentscope typically uses this format
            return SessionSummary(
                id=session_id,
                timestamp=timestamp,
                title=title,
                status=status,
                task_count=task_count
            )
        except Exception:
            return None
