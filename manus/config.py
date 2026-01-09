"""Configuration objects for Manus."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Sequence

DEFAULT_BASE_URL = "https://api.siliconflow.cn/v1"
DEFAULT_API_KEY = "YOUR_API_KEY_FROM_CLOUD_SILICONFLOW_CN"

def _env(key: str, fallback: str) -> str:
    value = os.getenv(key)
    if value:
        return value
    return fallback

@dataclass
class LLMConfig:
    """LLM connection details with safe defaults."""

    model: str = field(
        default_factory=lambda: _env("MANUS_MODEL", "deepseek-ai/DeepSeek-V3.1")
    )
    base_url: str = field(
        default_factory=lambda: _env("MANUS_LLM_BASE_URL", DEFAULT_BASE_URL)
    )
    api_key: str = field(
        default_factory=lambda: _env("MANUS_LLM_API_KEY", DEFAULT_API_KEY)
    )
    temperature: float = 0.2
    max_tokens: int = 1024
    timeout: float = 120.0

    def as_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

@dataclass
class ManusSettings:
    """Top level settings shared across Manus components."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    default_tools: Sequence[str] = field(default_factory=lambda: ["search", "calculator"])
    max_steps: int = 4

    def copy(self, **overrides) -> "ManusSettings":
        data = {
            "llm": overrides.get("llm", self.llm),
            "default_tools": overrides.get("default_tools", self.default_tools),
            "max_steps": overrides.get("max_steps", self.max_steps),
        }
        return ManusSettings(**data)
