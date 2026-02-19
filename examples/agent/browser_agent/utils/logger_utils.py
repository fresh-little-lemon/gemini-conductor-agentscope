# -*- coding: utf-8 -*-
"""Logging utilities for recording session logs in JSON format."""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from agentscope.agent import AgentBase

class SessionJSONLogger:
    """
    Manages a single JSON file for the session, recording metadata and a history of logs/prints.
    """
    def __init__(self, session_dir: str, session_id: str, metadata: Dict[str, Any]) -> None:
        self.session_id = session_id
        self.metadata = metadata
        self.history: List[Dict[str, Any]] = []
        
        # Determine log file path: sessions/{ts}/logs/runtime.json
        self.log_dir = os.path.join(session_dir, "logs")
        self.log_file = os.path.join(self.log_dir, "runtime.json")
        os.makedirs(self.log_dir, exist_ok=True)
        self._flush()

    def add_entry(self, entry: Dict[str, Any]) -> None:
        self.history.append(entry)
        self._flush()

    def _flush(self) -> None:
        data = {
            "session_id": self.session_id,
            "metadata": self.metadata,
            "history": self.history
        }
        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            # Fallback to stderr to avoid missing critical info if disk write fails
            import sys
            print(f"Error writing session log: {e}", file=sys.stderr)

class SessionJSONHandler(logging.Handler):
    """
    A logging handler that updates the SessionJSONLogger.
    """
    def __init__(self, session_logger: SessionJSONLogger) -> None:
        super().__init__()
        self.session_logger = session_logger

    def emit(self, record: logging.LogRecord) -> None:
        try:
            log_entry = {
                "type": "log",
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": self.format(record),
                "module": record.module,
                "funcName": record.funcName,
                "lineno": record.lineno,
            }
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)
            
            self.session_logger.add_entry(log_entry)
        except Exception:
            self.handleError(record)

def setup_session_logger(session_dir: str, session_id: str, metadata: Dict[str, Any], level: str = "INFO") -> None:
    """
    Sets up JSON logging for the session.
    Records both standard logger output and agent print messages into a structured JSON.
    
    Args:
        session_dir (`str`):
            The directory of the current session (e.g., sessions/{ts}).
        session_id (`str`):
            The ID of the current session.
        metadata (`Dict`):
            Metadata to include in the log file (e.g., CLI arguments).
        level (`str`, defaults to `"INFO"`):
            The logging level.
    """
    session_logger = SessionJSONLogger(session_dir, session_id, metadata)
    
    # 1. Capture standard agentscope logger output
    from agentscope._logging import logger as as_logger
    
    json_handler = SessionJSONHandler(session_logger)
    json_handler.setLevel(level)
    json_handler.setFormatter(logging.Formatter("%(message)s"))
    as_logger.addHandler(json_handler)
    
    # 2. Capture agent.print output via class hook
    def agent_print_hook(agent: AgentBase, kwargs: Dict, output: Any) -> None:
        msg = kwargs.get("msg")
        last = kwargs.get("last", True)
        
        # Only record complete messages to avoid cluttering with chunks
        if msg is None or not last:
            return
            
        entry = {
            "type": "print",
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent.name,
            "agent_id": agent.id,
            "message": msg.to_dict() if hasattr(msg, "to_dict") else str(msg)
        }
        
        session_logger.add_entry(entry)
            
    # Register hook for ALL agents (BrowserAgent, UserAgent, etc.)
    AgentBase.register_class_hook("post_print", "json_log_recorder", agent_print_hook)
