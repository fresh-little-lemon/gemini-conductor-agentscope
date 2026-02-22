# -*- coding: utf-8 -*-
"""Token usage and performance tracker with persistent logging and robust interceptors."""

import os
import time
import json
import inspect
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional, Union, AsyncGenerator, AsyncIterator

from agentscope.token import TokenCounterBase
from agentscope.model import ChatResponse, ChatModelBase
from agentscope.model._model_usage import ChatUsage
from agentscope.tool import Toolkit, ToolResponse
from agentscope.message import ToolUseBlock
from agentscope import _config

class ModelWrapper:
    """
    A proxy wrapper for ChatModelBase instances to ensure all calls 
    (including direct __call__) are intercepted for tracking.
    """
    def __init__(self, model: ChatModelBase, tracker: 'TokenUsageTracker'):
        self._model = model
        self._tracker = tracker
        # Essential attributes for AgentScope agents
        self.model_name = getattr(model, "model_name", "unknown")
        self.stream = getattr(model, "stream", False)

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return await self._tracker._tracked_model_call(self._model, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._model, name)

class TokenUsageTracker(TokenCounterBase):
    """
    A tracker class to monitor and record token usage, API performance, 
    and tool execution metrics. Logs detailed data to session_logs/.
    """
    def __init__(self) -> None:
        self.stats: Dict[str, Dict[str, Any]] = {}
        self.total_api_time = 0.0
        self.total_tool_time = 0.0
        self.agent_active_time = 0.0
        self.start_wall_time = time.time()
        self.tool_calls_count = 0
        self.successful_tool_calls = 0
        self.failed_tool_calls = 0
        self._current_reply_start: float = 0.0
        
        # Setup logging directory
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = os.path.join("sessions", self.timestamp)
        self.log_dir = os.path.join(self.session_dir, "traces")
        self.request_index = 0

    async def count(self, messages: list[dict], **kwargs: Any) -> int:
        """Required by TokenCounterBase."""
        return 0

    def _log_to_file(self, prefix: str, data: Any) -> None:
        """Logs data to a JSON file in the session directory."""
        self.request_index += 1
        filename = f"{self.request_index:03d}_{prefix}.json"
        filepath = os.path.join(self.log_dir, filename)
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"Error logging to {filepath}: {e}")

    def record_usage(self, model_name: str, usage: Any = None) -> None:
        """Record usage metrics from a usage object or dict."""
        if model_name not in self.stats:
            self.stats[model_name] = {
                "reqs": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "api_time": 0.0
            }
        
        self.stats[model_name]["reqs"] += 1
        
        if usage:
            # Use dictionary access for ChatUsage/DictMixin to be safe
            def get_val(obj, key, default=0):
                try:
                    if isinstance(obj, dict):
                        return obj.get(key, default)
                    return getattr(obj, key, default)
                except Exception:
                    return default

            it = get_val(usage, "input_tokens", 0)
            ot = get_val(usage, "output_tokens", 0)
            at = get_val(usage, "time", 0.0)
            
            self.stats[model_name]["input_tokens"] += it
            self.stats[model_name]["output_tokens"] += ot
            self.stats[model_name]["api_time"] += at
            self.total_api_time += at

    def track_model(self, model: ChatModelBase) -> ChatModelBase:
        """Returns a wrapped model instance that tracks all calls."""
        return ModelWrapper(model, self) # type: ignore

    async def _tracked_model_call(self, model: ChatModelBase, *args: Any, **kwargs: Any) -> Any:
        """Internal helper to handle the actual tracking logic for model calls."""
        model_name = getattr(model, "model_name", "unknown")
        input_data = {"args": args, "kwargs": kwargs}
        
        start_time = time.time()
        res = await model(*args, **kwargs)
        
        # Safe check for async iterator without triggering DictMixin.__getattr__
        if inspect.isasyncgen(res) or hasattr(type(res), "__anext__"):
            return self._wrap_stream(model_name, input_data, res)
        else:
            usage_data = getattr(res, "usage", None)
            self.record_usage(model_name, usage_data)
            self._log_to_file(f"model_{model_name}", {
                "input": input_data,
                "output": getattr(res, "content", None),
                "usage": usage_data,
                "latency": time.time() - start_time
            })
            return res

    async def _wrap_stream(self, model_name: str, input_data: Any, stream: AsyncIterator[ChatResponse]) -> AsyncGenerator[ChatResponse, None]:
        """Intercepts chunks from a streaming response to capture final usage."""
        last_usage = None
        full_content = []
        
        async for chunk in stream:
            # Safely check for usage in chunk
            usage = getattr(chunk, "usage", None)
            if usage:
                last_usage = usage
            if hasattr(chunk, "content") and chunk.content:
                full_content.append(chunk.content)
            yield chunk
        
        self.record_usage(model_name, last_usage)
        self._log_to_file(f"model_{model_name}_stream", {
            "input": input_data,
            "output": full_content,
            "usage": last_usage
        })

    def track_toolkit(self, toolkit: Toolkit) -> Toolkit:
        """Wrap Toolkit.call_tool_function to track tool execution and success."""
        original_call = toolkit.call_tool_function
        tracker_self = self

        @wraps(original_call)
        async def tracked_call(tool_call: ToolUseBlock) -> AsyncGenerator[ToolResponse, None]:
            tracker_self.tool_calls_count += 1
            start_time = time.time()
            
            gen = await original_call(tool_call)
            
            async def wrapped_gen():
                success = True
                full_output = []
                async for chunk in gen:
                    if getattr(chunk, "is_interrupted", False):
                        success = False
                    for block in chunk.content:
                        full_output.append(block)
                        if block.get("type") == "text":
                            text = block.get("text", "").lower()
                            if any(err in text for err in ["error", "not found", "failed", "exception"]):
                                success = False
                    yield chunk
                
                duration = time.time() - start_time
                tracker_self.total_tool_time += duration
                if success:
                    tracker_self.successful_tool_calls += 1
                else:
                    tracker_self.failed_tool_calls += 1
                
                tracker_self._log_to_file(f"tool_{tool_call.get('name')}", {
                    "call": tool_call,
                    "output": full_output,
                    "duration": duration,
                    "success": success
                })

            return wrapped_gen()

        toolkit.call_tool_function = tracked_call
        return toolkit

    def get_agent_hooks(self) -> Dict[str, Any]:
        """Returns hooks to measure Agent Active time."""
        async def pre_reply(agent: Any, kwargs: Dict) -> Dict:
            self._current_reply_start = time.time()
            return kwargs
            
        async def post_reply(agent: Any, kwargs: Dict, output: Any) -> Any:
            self.agent_active_time += time.time() - self._current_reply_start
            return output
            
        return {
            "pre_reply": pre_reply,
            "post_reply": post_reply
        }

    def get_summary_dict(self) -> Dict[str, Any]:
        """Returns a dictionary containing all tracked metrics."""
        wall_time = time.time() - self.start_wall_time
        success_rate = (self.successful_tool_calls / self.tool_calls_count * 100) if self.tool_calls_count > 0 else 0
        
        return {
            "run_id": _config.run_id,
            "tool_calls": {
                "total": self.tool_calls_count,
                "successful": self.successful_tool_calls,
                "failed": self.failed_tool_calls,
                "success_rate": round(success_rate, 2)
            },
            "performance": {
                "wall_time": round(wall_time, 2),
                "agent_active_time": round(self.agent_active_time, 2),
                "api_time": round(self.total_api_time, 2),
                "tool_time": round(self.total_tool_time, 2),
                "api_percent": round((self.total_api_time / self.agent_active_time * 100), 2) if self.agent_active_time > 0 else 0,
                "tool_percent": round((self.total_tool_time / self.agent_active_time * 100), 2) if self.agent_active_time > 0 else 0
            },
            "model_usage": self.stats
        }

    def show_summary(self) -> None:
        """Prints a visual interaction summary."""
        wall_time = time.time() - self.start_wall_time
        
        def format_duration(seconds: float) -> str:
            if seconds < 1:
                return f"{int(seconds * 1000)}ms"
            m, s = divmod(int(seconds), 60)
            if m > 0:
                return f"{m}m {s}s"
            return f"{s:.1f}s"

        GREEN = "\033[92m"
        BLUE = "\033[94m"
        BOLD = "\033[1m"
        RESET = "\033[0m"

        print(f"\n{BLUE}Agent powering down. Goodbye!{RESET}")
        print(f"Detailed logs saved to: {self.log_dir}")
        print(f"\n{BOLD}Interaction Summary{RESET}")
        print(f"Session ID:          {self.timestamp}_{_config.run_id}")
        print(f"Tool Calls:          {self.tool_calls_count} ( {GREEN}✓ {self.successful_tool_calls}{RESET} x {self.failed_tool_calls} )")
        success_rate = (self.successful_tool_calls / self.tool_calls_count * 100) if self.tool_calls_count > 0 else 0
        print(f"Success Rate:        {GREEN}{success_rate:.1f}%{RESET}")
        
        print(f"\n{BOLD}Performance{RESET}")
        print(f"Wall Time:           {format_duration(wall_time)}")
        print(f"Agent Active:        {format_duration(self.agent_active_time)}")
        api_percent = (self.total_api_time / self.agent_active_time * 100) if self.agent_active_time > 0 else 0
        print(f"  » API Time:        {format_duration(self.total_api_time)} ({api_percent:.1f}%)")
        tool_percent = (self.total_tool_time / self.agent_active_time * 100) if self.agent_active_time > 0 else 0
        print(f"  » Tool Time:       {format_duration(self.total_tool_time)} ({tool_percent:.1f}%)")
        
        print(f"\n{BOLD}Model Usage{RESET}")
        print(f"{'Model':<30} {'Reqs':>5} {'Input Tokens':>15} {'Output Tokens':>15}")
        print("-" * 70)
        for model, data in self.stats.items():
            print(f"{model:<30} {data['reqs']:>5} {data['input_tokens']:>15,} {data['output_tokens']:>15,}")
        print("-" * 70 + "\n")
