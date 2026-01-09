"""Tool registry exports."""

from .base import Tool, ToolInput, ToolOutput, ToolRegistry
from .calculator import CalculatorTool
from .functools_component import register_functools_tools
from .local_search import LocalSearchTool

__all__ = [
    "Tool",
    "ToolInput",
    "ToolOutput",
    "ToolRegistry",
    "LocalSearchTool",
    "CalculatorTool",
    "register_functools_tools",
    "build_default_registry",
]

def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(LocalSearchTool())
    registry.register(CalculatorTool())
    register_functools_tools(registry)
    return registry
