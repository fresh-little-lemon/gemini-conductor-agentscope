import os
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class SessionSummary(BaseModel):
    id: str
    timestamp: str
    title: str
    status: str
    task_count: int

class SessionDetails(BaseModel):
    id: str
    plan: Optional[Dict[str, Any]] = None
    results: List[Dict[str, Any]] = []
    report: Optional[str] = None
    artifacts: List[Dict[str, Any]] = []

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
                summary = self._parse_session_summary(session_id, path)
                if summary:
                    summaries.append(summary)
        
        # Sort by timestamp descending (assuming folder names start with timestamp)
        summaries.sort(key=lambda x: x.id, reverse=True)
        return summaries

    def _parse_session_summary(self, session_id: str, path: str) -> SessionSummary | None:
        results_path = os.path.join(path, "results.json")
        try:
            timestamp = session_id # Folders are usually YYYY-MM-DD_HH-MM-SS
            title = session_id
            status = "completed" if os.path.exists(os.path.join(path, "report.md")) else "in_progress"
            task_count = 0
            
            if os.path.exists(results_path):
                with open(results_path, "r", encoding="utf-8") as f:
                    results = json.load(f)
                    task_count = len(results)
            
            return SessionSummary(
                id=session_id,
                timestamp=timestamp,
                title=title,
                status=status,
                task_count=task_count
            )
        except Exception:
            return None

    def get_session_details(self, session_id: str) -> Optional[SessionDetails]:
        path = os.path.join(self.sessions_dir, session_id)
        if not os.path.isdir(path):
            return None
            
        details = SessionDetails(id=session_id)
        
        # Load results.json
        results_path = os.path.join(path, "results.json")
        if os.path.exists(results_path):
            with open(results_path, "r", encoding="utf-8") as f:
                details.results = json.load(f)
                
        # Load report.md
        report_path = os.path.join(path, "report.md")
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                details.report = f.read()
                
        # Discover artifacts (exploration/subagent_*/...)
        exploration_dir = os.path.join(path, "exploration")
        if os.path.isdir(exploration_dir):
            for agent_dir in os.listdir(exploration_dir):
                agent_path = os.path.join(exploration_dir, agent_dir)
                if os.path.isdir(agent_path):
                    # We can list files here as artifacts
                    for filename in os.listdir(agent_path):
                        if filename.endswith(('.png', '.mp4', '.json', '.md')):
                            details.artifacts.append({
                                "name": f"{agent_dir}/{filename}",
                                "path": os.path.join(agent_path, filename),
                                "type": filename.split('.')[-1]
                            })
                            
        return details
