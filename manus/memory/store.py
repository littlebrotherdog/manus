"""Simple in-memory event store inspired by super-agent's Memory schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List

@dataclass
class MemoryEvent:
    role: str
    content: str
    metadata: dict[str, Any] | None = field(default_factory=dict)

class MemoryStore:
    def __init__(self):
        self._events: List[MemoryEvent] = []

    def add(self, role: str, content: str, *, metadata: dict[str, Any] | None = None) -> None:
        event = MemoryEvent(role=role, content=content, metadata=metadata or {})
        self._events.append(event)

    def extend(self, events: Iterable[MemoryEvent]) -> None:
        for event in events:
            self._events.append(event)

    def tail(self, limit: int = 10) -> List[MemoryEvent]:
        return self._events[-limit:]

    def as_prompt(self, limit: int = 10) -> list[dict[str, str]]:
        return [{"role": e.role, "content": e.content} for e in self.tail(limit)]

    def clear(self) -> None:
        self._events.clear()

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._events)
