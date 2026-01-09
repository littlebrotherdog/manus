"""LLM protocol definitions used across Manus."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

@dataclass
class ChatMessage:
    role: str
    content: str

@dataclass
class ChatCompletion:
    content: str
    raw: dict[str, Any]

class LLMClient:
    """Abstract base class for chat completion providers."""

    async def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float,
        max_tokens: int,
        model: str,
    ) -> ChatCompletion:
        raise NotImplementedError
