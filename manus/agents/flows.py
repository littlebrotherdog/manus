"""Data classes describing planning and events."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

@dataclass
class PlanStep:
    index: int
    instruction: str
    suggested_tool: Optional[str] = None

@dataclass
class Plan:
    task: str
    steps: List[PlanStep]
    raw_text: str

@dataclass
class AgentEvent:
    type: str
    message: str
    payload: dict[str, Any] | None = field(default_factory=dict)
