"""Tool registry exports."""

from .base import Tool, ToolInput, ToolOutput, ToolRegistry
from .calculator import CalculatorTool
from .local_search import LocalSearchTool

__all__ = [
    "Tool",
    "ToolInput",
    "ToolOutput",
    "ToolRegistry",
    "LocalSearchTool",
    "CalculatorTool",
    "build_default_registry",
]

def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(LocalSearchTool())
    registry.register(CalculatorTool())
    return registry
