# -*- coding: utf-8 -*-
"""Token usage and performance tracker with persistent logging and robust interceptors."""

import os
import time
import json
import inspect
from datetime import datetime
from functools import wraps
from dataclasses import is_dataclass, asdict
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
    and tool execution metrics. Logs detailed data to sessions/.
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
        os.makedirs(self.log_dir, exist_ok=True)
        self.request_index = 0

    async def count(self, messages: list[dict], **kwargs: Any) -> int:
        """Required by TokenCounterBase."""
        return 0

    def _log_to_file(self, prefix: str, data: Any) -> None:
        """Logs data to a JSON file in the session directory with robust serialization."""
        self.request_index += 1
        filename = f"{self.request_index:03d}_{prefix}.json"
        filepath = os.path.join(self.log_dir, filename)
        
        def serialize(obj):
            """Custom serializer to capture raw response data from SDK objects."""
            if is_dataclass(obj):
                return asdict(obj)
            if hasattr(obj, "model_dump") and callable(obj.model_dump):
                return obj.model_dump()
            if hasattr(obj, "to_dict") and callable(obj.to_dict):
                return obj.to_dict()
            if hasattr(obj, "dict") and callable(obj.dict):
                return obj.dict()
            if hasattr(obj, "__dict__"):
                return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
            return str(obj)

        try:
            os.makedirs(self.log_dir, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=serialize)
        except Exception as e:
            print(f"Error logging to {filepath}: {e}")

    def record_usage(self, model_name: str, usage: Any = None, raw_api_response: Any = None) -> None:
        """Record usage metrics from a usage object, dict, or raw API response."""
        if model_name not in self.stats:
            self.stats[model_name] = {
                "reqs": 0,
                "input_tokens": 0,
                "cached_tokens": 0,
                "output_tokens": 0,
                "api_time": 0.0
            }
        
        self.stats[model_name]["reqs"] += 1
        
        if usage or raw_api_response:
            def safe_get(obj, key, default=None):
                if obj is None: return default
                if isinstance(obj, dict): return obj.get(key, default)
                try: return getattr(obj, key, default)
                except Exception: return default

            it = safe_get(usage, "input_tokens", 0) or 0
            ot = safe_get(usage, "output_tokens", 0) or 0
            at = safe_get(usage, "time", 0.0) or 0.0
            
            cached = 0
            # Path 1: AgentScope ChatUsage.metadata
            metadata = safe_get(usage, "metadata", None)
            if metadata:
                prompt_details = safe_get(metadata, "prompt_tokens_details", None)
                if prompt_details:
                    cached = safe_get(prompt_details, "cached_tokens", 0) or 0
            
            # Path 2: Raw API Response usage (OpenAI/DashScope compatible)
            if cached == 0 and raw_api_response:
                raw_usage = safe_get(raw_api_response, "usage", None)
                if raw_usage:
                    prompt_details = safe_get(raw_usage, "prompt_tokens_details", None)
                    if prompt_details:
                        cached = safe_get(prompt_details, "cached_tokens", 0) or 0
                    elif it == 0: # If AgentScope usage was empty, try to get totals from raw too
                        it = safe_get(raw_usage, "prompt_tokens", 0) or 0
                        ot = safe_get(raw_usage, "completion_tokens", 0) or 0
            
            # Ensure we don't have negative input tokens
            uncached_input = max(0, it - cached)
            
            self.stats[model_name]["input_tokens"] += uncached_input
            self.stats[model_name]["cached_tokens"] += cached
            self.stats[model_name]["output_tokens"] += ot
            self.stats[model_name]["api_time"] += at
            self.total_api_time += at

    def track_model(self, model: ChatModelBase) -> ChatModelBase:
        """Returns a wrapped model instance that tracks all calls and raw API responses."""
        self._wrap_model_client(model)
        return ModelWrapper(model, self) # type: ignore

    def _wrap_model_client(self, model: ChatModelBase):
        """DEFENSIVELY monkey-patch underlying SDK clients to capture TRUE raw API responses."""
        try:
            # OpenAI / DashScope Compatible / vLLM / DeepSeek
            if hasattr(model, "client") and hasattr(model.client, "chat") and hasattr(model.client.chat, "completions"):
                client = model.client
                
                def make_wrapper(orig_method):
                    @wraps(orig_method)
                    async def wrapped_method(*args, **kwargs):
                        raw_res = await orig_method(*args, **kwargs)
                        client._last_raw_response = raw_res
                        return raw_res
                    return wrapped_method

                for method_name in ["create", "parse"]:
                    if hasattr(client.chat.completions, method_name):
                        orig = getattr(client.chat.completions, method_name)
                        setattr(client.chat.completions, method_name, make_wrapper(orig))
            
            # Google Gemini
            if hasattr(model, "client") and hasattr(model.client, "aio") and hasattr(model.client.aio, "models"):
                client = model.client
                orig_gen = client.aio.models.generate_content
                @wraps(orig_gen)
                async def wrapped_gen(*args, **kwargs):
                    raw_res = await orig_gen(*args, **kwargs)
                    client._last_raw_response = raw_res
                    return raw_res
                client.aio.models.generate_content = wrapped_gen
        except Exception:
            pass

    async def _tracked_model_call(self, model: ChatModelBase, *args: Any, **kwargs: Any) -> Any:
        """Internal helper to handle the actual tracking logic for model calls."""
        model_name = getattr(model, "model_name", "unknown")
        input_data = {"args": args, "kwargs": kwargs}
        
        start_time = time.time()
        res = await model(*args, **kwargs)
        
        # Capture the raw response saved by our monkey-patch
        raw_api_response = None
        if hasattr(model, "client") and hasattr(model.client, "_last_raw_response"):
            raw_api_response = model.client._last_raw_response

        if inspect.isasyncgen(res) or hasattr(type(res), "__anext__"):
            return self._wrap_stream(model_name, input_data, res)
        else:
            usage_data = getattr(res, "usage", None)
            self.record_usage(model_name, usage_data, raw_api_response)
            
            log_data = {
                "agentscope_id": getattr(res, "id", None),
                "model": model_name,
                "input": input_data,
                "output": getattr(res, "content", None),
                "usage": usage_data,
                "response_metadata": getattr(res, "metadata", None),
                "raw_api_response": raw_api_response,
                "latency": time.time() - start_time
            }
            self._log_to_file(f"model_{model_name}", log_data)
            return res

    async def _wrap_stream(self, model_name: str, input_data: Any, stream: AsyncIterator[ChatResponse]) -> AsyncGenerator[ChatResponse, None]:
        """Intercepts chunks from a streaming response to capture final usage."""
        last_usage = None
        full_content = []
        last_chunk = None
        
        async for chunk in stream:
            last_chunk = chunk
            try:
                usage = chunk.get("usage") if isinstance(chunk, dict) else getattr(chunk, "usage", None)
                if usage: last_usage = usage
            except Exception: pass
            if hasattr(chunk, "content") and chunk.content:
                full_content.append(chunk.content)
            yield chunk
        
        self.record_usage(model_name, last_usage)
        self._log_to_file(f"model_{model_name}_stream", {
            "input": input_data,
            "output": full_content,
            "usage": last_usage,
            "response_metadata": getattr(last_chunk, "metadata", None)
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
                    if getattr(chunk, "is_interrupted", False): success = False
                    for block in chunk.content:
                        full_output.append(block)
                        if block.get("type") == "text":
                            text = block.get("text", "").lower()
                            if any(err in text for err in ["error", "not found", "failed", "exception"]):
                                success = False
                    yield chunk
                
                duration = time.time() - start_time
                tracker_self.total_tool_time += duration
                if success: tracker_self.successful_tool_calls += 1
                else: tracker_self.failed_tool_calls += 1
                
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
        return {"pre_reply": pre_reply, "post_reply": post_reply}

    def get_summary_dict(self) -> Dict[str, Any]:
        """Returns a dictionary containing all tracked metrics."""
        wall_time = time.time() - self.start_wall_time
        success_rate = (self.successful_tool_calls / self.tool_calls_count * 100) if self.tool_calls_count > 0 else 0
        return {
            "run_id": _config.run_id,
            "timestamp": self.timestamp,
            "tool_calls": {"total": self.tool_calls_count, "successful": self.successful_tool_calls, "failed": self.failed_tool_calls, "success_rate": round(success_rate, 2)},
            "performance": {"wall_time": round(wall_time, 2), "agent_active_time": round(self.agent_active_time, 2), "api_time": round(self.total_api_time, 2), "tool_time": round(self.total_tool_time, 2)},
            "model_usage": self.stats
        }

    def show_summary(self) -> None:
        """Prints a visual interaction summary matching the theme and thresholds."""
        from .terminal_theme import get_theme
        theme = get_theme()
        wall_time = time.time() - self.start_wall_time
        
        # Color Palette (Dynamic from terminal background)
        ACCENT_BLUE = theme.accent_blue
        ACCENT_GREEN = theme.accent_green
        ACCENT_YELLOW = theme.accent_yellow
        ACCENT_RED = theme.accent_red
        BORDER = theme.border_default
        
        # Gradient stops
        STOPS = theme.gradient_stops

        def to_ansi(rgb: tuple) -> str:
            return f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"

        BLUE_ANSI = to_ansi(ACCENT_BLUE)
        GREEN_ANSI = to_ansi(ACCENT_GREEN)
        YELLOW_ANSI = to_ansi(ACCENT_YELLOW)
        RED_ANSI = to_ansi(ACCENT_RED)
        BORDER_ANSI = to_ansi(BORDER)
        BOLD = "\033[1m"
        RESET = "\033[0m"
        LINE_CHAR = "\u2500"

        def get_status_color(value: float, high: float, med: float) -> str:
            if value >= high: return GREEN_ANSI
            if value >= med: return YELLOW_ANSI
            return RED_ANSI

        def format_duration(seconds: float) -> str:
            if seconds < 1: return f"{int(seconds * 1000)}ms"
            m, s = divmod(int(seconds), 60)
            return f"{m}m {s}s" if m > 0 else f"{s:.1f}s"

        def get_gradient_text(text: str) -> str:
            """Smooth 3-point RGB gradient interpolation."""
            result = ""
            n = len(text)
            for i, char in enumerate(text):
                ratio = i / max(1, n - 1)
                if ratio <= 0.5:
                    sub_ratio = ratio * 2
                    r = int(STOPS[0][0] + (STOPS[1][0] - STOPS[0][0]) * sub_ratio)
                    g = int(STOPS[0][1] + (STOPS[1][1] - STOPS[0][1]) * sub_ratio)
                    b = int(STOPS[0][2] + (STOPS[1][2] - STOPS[0][2]) * sub_ratio)
                else:
                    sub_ratio = (ratio - 0.5) * 2
                    r = int(STOPS[1][0] + (STOPS[2][0] - STOPS[1][0]) * sub_ratio)
                    g = int(STOPS[1][1] + (STOPS[2][1] - STOPS[1][1]) * sub_ratio)
                    b = int(STOPS[1][2] + (STOPS[2][2] - STOPS[1][2]) * sub_ratio)
                result += f"\033[38;2;{r};{g};{b}m{char}"
            return result + RESET

        print(f"\n{get_gradient_text('Agent powering down. Goodbye!')}")
        
        print(f"\n{BOLD}Interaction Summary{RESET}")
        print(f"{BLUE_ANSI}Session ID:{RESET}          {self.timestamp}_{_config.run_id}")
        print(f"{BLUE_ANSI}Tool Calls:{RESET}          {self.tool_calls_count} ( {GREEN_ANSI}\u2713 {self.successful_tool_calls}{RESET} {RED_ANSI}x {self.failed_tool_calls}{RESET} )")
        success_rate = (self.successful_tool_calls / self.tool_calls_count * 100) if self.tool_calls_count > 0 else 0
        rate_color = get_status_color(success_rate, 95, 85)
        print(f"{BLUE_ANSI}Success Rate:{RESET}        {rate_color}{success_rate:.1f}%{RESET}")

        print(f"\n{BOLD}Performance{RESET}")
        print(f"{BLUE_ANSI}Wall Time:{RESET}           {format_duration(wall_time)}")
        print(f"{BLUE_ANSI}Agent Active:{RESET}        {format_duration(self.agent_active_time)}")
        
        if self.agent_active_time > 0:
            api_percent = (self.total_api_time / self.agent_active_time * 100)
            tool_percent = (self.total_tool_time / self.agent_active_time * 100)
            print(f"  \u00bb API Time:        {format_duration(self.total_api_time)} ({api_percent:.1f}%)")
            print(f"  \u00bb Tool Time:       {format_duration(self.total_tool_time)} ({tool_percent:.1f}%)")

        if self.stats:
            print(f"\n{BOLD}Model Usage{RESET}")
            has_cache = any(data.get('cached_tokens', 0) > 0 for data in self.stats.values())
            
            w_model, w_reqs, w_input, w_cache, w_output = 18, 6, 15, 15, 15
            def pad_bold(text: str, width: int, align: str = "left") -> str:
                if align == "left":
                    return f"{BOLD}{text}{RESET}".ljust(width + 8)
                else:
                    return f"{BOLD}{text}{RESET}".rjust(width + 8)

            if has_cache:
                header_str = f"{pad_bold('Model', w_model)} {pad_bold('Reqs', w_reqs, 'right')} {pad_bold('Input Tokens', w_input, 'right')} {pad_bold('Cache Reads', w_cache, 'right')} {pad_bold('Output Tokens', w_output, 'right')}"
                total_width = w_model + w_reqs + w_input + w_cache + w_output + 4
            else:
                header_str = f"{pad_bold('Model', w_model)} {pad_bold('Reqs', w_reqs, 'right')} {pad_bold('Input Tokens', w_input, 'right')} {pad_bold('Output Tokens', w_output, 'right')}"
                total_width = w_model + w_reqs + w_input + w_output + 3

            print(header_str)
            print(f"{BORDER_ANSI}{LINE_CHAR * total_width}{RESET}")

            total_input, total_cached = 0, 0
            for model, data in self.stats.items():
                it, ct, ot, reqs = data.get('input_tokens', 0), data.get('cached_tokens', 0), data.get('output_tokens', 0), data.get('reqs', 0)
                total_input += it; total_cached += ct
                if has_cache: print(f"{model:<{w_model}} {reqs:>{w_reqs}} {it:>{w_input},} {ct:>{w_cache},} {ot:>{w_output},}")
                else: print(f"{model:<{w_model}} {reqs:>{w_reqs}} {it:>{w_input},} {ot:>{w_output},}")

            if has_cache and (total_input + total_cached > 0):
                savings_pct = (total_cached / (total_input + total_cached)) * 100
                savings_color = get_status_color(savings_pct, 40, 15)
                print(f"\n{GREEN_ANSI}Savings Highlight:{RESET} {total_cached:,} ({savings_color}{savings_pct:.1f}%{RESET}) of input tokens were served from the cache, reducing costs.")
        print()
        print()
