"""Tool contracts and registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Protocol

@dataclass
class ToolInput:
    task: str
    context: Dict[str, Any]

@dataclass
class ToolOutput:
    content: str
    metadata: Dict[str, Any]

class Tool(Protocol):
    name: str
    description: str

    async def arun(self, tool_input: ToolInput) -> ToolOutput:
        ...

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not registered")
        return self._tools[name]

    def listed(self) -> list[str]:
        return sorted(self._tools)

    def as_prompt_block(self) -> str:
        lines = []
        for key in self.listed():
            tool = self._tools[key]
            lines.append(f"- {tool.name}: {tool.description}")
        return "\n".join(lines)


class FunctionTool:
    """Wraps coroutine functions into the Tool protocol."""

    def __init__(
        self,
        *,
        name: str,
        description: str,
        func: Callable[[ToolInput], Awaitable[ToolOutput]],
    ):
        self.name = name
        self.description = description
        self._func = func

    async def arun(self, tool_input: ToolInput) -> ToolOutput:  # pragma: no cover - thin wrapper
        return await self._func(tool_input)
