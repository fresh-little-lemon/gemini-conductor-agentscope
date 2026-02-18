# -*- coding: utf-8 -*-
"""Auto-model and Auto-formatter loader for AgentScope."""

import json
import os
from typing import Any, Dict, Type

from agentscope.model import (
    DashScopeChatModel,
    OpenAIChatModel,
    AnthropicChatModel,
    OllamaChatModel,
    GeminiChatModel,
    ChatModelBase
)
from agentscope.formatter import (
    DashScopeChatFormatter,
    AnthropicChatFormatter,
    OpenAIChatFormatter,
    GeminiChatFormatter,
    OllamaChatFormatter,
    DeepSeekChatFormatter,
    FormatterBase
)

MODEL_MAP: Dict[str, Type[ChatModelBase]] = {
    "dashscope": DashScopeChatModel,
    "openai": OpenAIChatModel,
    "anthropic": AnthropicChatModel,
    "ollama": OllamaChatModel,
    "gemini": GeminiChatModel,
}

FORMATTER_MAP: Dict[str, Type[FormatterBase]] = {
    "dashscope": DashScopeChatFormatter,
    "anthropic": AnthropicChatFormatter,
    "openai": OpenAIChatFormatter,
    "gemini": GeminiChatFormatter,
    "ollama": OllamaChatFormatter,
    "deepseek": DeepSeekChatFormatter,
}

def load_config(config_path: str) -> dict:
    """Load configuration from a JSON file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

class AutoModel:
    """AutoModel class for loading models from configuration."""

    @classmethod
    def from_config(cls, config_path: str) -> ChatModelBase:
        """
        Load a model from a configuration file.

        Args:
            config_path (`str`):
                Path to the configuration file (JSON).

        Returns:
            `ChatModelBase`:
                The loaded model instance.
        """
        config = load_config(config_path)
        model_type = config.get("model_type")
        if not model_type:
            raise ValueError("model_type must be specified in the configuration.")

        model_cls = MODEL_MAP.get(model_type.lower())
        if not model_cls:
            raise ValueError(f"Unsupported model type: {model_type}")

        # Extract arguments and handle defaults
        model_name = config.get("model_name")
        if not model_name:
            raise ValueError("model_name must be specified in the configuration.")

        # Optional arguments with defaults in the model classes
        kwargs = {}
        if "api_key" in config:
            kwargs["api_key"] = config["api_key"]
        if "stream" in config:
            kwargs["stream"] = config["stream"]
        if "client_kwargs" in config:
            kwargs["client_kwargs"] = config["client_kwargs"]
        if "generate_kwargs" in config:
            kwargs["generate_kwargs"] = config["generate_kwargs"]

        # Handle model-specific parameters if any (e.g., enable_thinking for DashScope)
        for key in ["enable_thinking", "multimodality", "max_tokens", "thinking", "thinking_config", "options", "keep_alive", "host"]:
            if key in config:
                kwargs[key] = config[key]

        return model_cls(model_name=model_name, **kwargs)

class AutoFormatter:
    """AutoFormatter class for loading formatters from configuration."""

    @classmethod
    def from_config(cls, config_path: str) -> FormatterBase:
        """
        Load a formatter from a configuration file.

        Args:
            config_path (`str`):
                Path to the configuration file (JSON).

        Returns:
            `FormatterBase`:
                The loaded formatter instance.
        """
        config = load_config(config_path)
        model_type = config.get("model_type")
        if not model_type:
            raise ValueError("model_type must be specified in the configuration.")

        formatter_cls = FORMATTER_MAP.get(model_type.lower())
        if not formatter_cls:
            # Fallback to OpenAI if not specifically mapped, or raise error
            formatter_cls = OpenAIChatFormatter

        formatter_kwargs = config.get("formatter_kwargs", {})
        return formatter_cls(**formatter_kwargs)
