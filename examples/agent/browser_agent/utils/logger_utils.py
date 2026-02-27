import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextvars import ContextVar
from agentscope.agent import AgentBase

# Context variable to store the logger for the current task/thread
session_context: ContextVar[Optional["SessionJSONLogger"]] = ContextVar(
    "session_context",
    default=None,
)

class SessionJSONLogger:
    """
    Manages a single JSON file for the session, recording metadata and a history of logs/prints.
    """
    def __init__(self, session_dir: str, session_id: str, metadata: Dict[str, Any]) -> None:
        self.session_id = session_id
        self.metadata = metadata
        self.history: List[Dict[str, Any]] = []
        self.summary: Dict[str, Any] = {}
        
        # Determine log file path: sessions/{ts}/logs/runtime.json
        self.log_dir = os.path.join(session_dir, "logs")
        self.log_file = os.path.join(self.log_dir, "runtime.json")
        os.makedirs(self.log_dir, exist_ok=True)
        self._flush()

    def add_entry(self, entry: Dict[str, Any]) -> None:
        self.history.append(entry)
        self._flush()

    def set_summary(self, summary: Dict[str, Any]) -> None:
        self.summary = summary
        self._flush()

    def _flush(self) -> None:
        data = {
            "session_id": self.session_id,
            "metadata": self.metadata,
            "history": self.history,
            "summary": self.summary
        }
        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            # Fallback to stderr to avoid missing critical info if disk write fails
            import sys
            print(f"Error writing session log: {e}", file=sys.stderr)

class GlobalSessionJSONHandler(logging.Handler):
    """
    A global logging handler that routes log records to the logger
    stored in the current context variable.
    """
    def emit(self, record: logging.LogRecord) -> None:
        logger_inst = session_context.get()
        if logger_inst is None:
            return

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
            
            logger_inst.add_entry(log_entry)
        except Exception:
            self.handleError(record)

# Singleton list to track if global handler is already added
_GLOBAL_HANDLER_ADDED = False

def setup_session_logger(session_dir: str, session_id: str, metadata: Dict[str, Any], level: str = "INFO") -> SessionJSONLogger:
    """
    Sets up JSON logging for the session using context-aware routing.
    
    Args:
        session_dir (`str`):
            The directory of the current session (e.g., sessions/{ts}).
        session_id (`str`):
            The ID of the current session.
        metadata (`Dict`):
            Metadata to include in the log file (e.g., CLI arguments).
        level (`str`, defaults to `"INFO"`):
            The logging level.

    Returns:
        SessionJSONLogger:
            The session logger instance.
    """
    global _GLOBAL_HANDLER_ADDED
    session_logger = SessionJSONLogger(session_dir, session_id, metadata)
    
    # Capture standard agentscope logger output via a global handler once
    from agentscope._logging import logger as as_logger
    
    if not _GLOBAL_HANDLER_ADDED:
        json_handler = GlobalSessionJSONHandler()
        json_handler.setLevel(level)
        json_handler.setFormatter(logging.Formatter("%(message)s"))
        as_logger.addHandler(json_handler)
        _GLOBAL_HANDLER_ADDED = True
    
    # Note: Agent print output should now be captured via instance hooks
    # in the agents using the following helper:
    # def agent_print_hook(agent, kwargs, output): ...
    # agent.register_instance_hook("post_print", "json_log", agent_print_hook)

    return session_logger

def get_agent_print_hook(session_logger: SessionJSONLogger):
    """Returns a print hook function bound to the given session logger."""
    def agent_print_hook(agent: AgentBase, kwargs: Dict, output: Any) -> None:
        msg = kwargs.get("msg")
        last = kwargs.get("last", True)
        
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
    
    return agent_print_hook

