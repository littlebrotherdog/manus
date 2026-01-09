"""Deterministic math helper."""

from __future__ import annotations

import ast
import operator

from .base import Tool, ToolInput, ToolOutput

_ALLOWED_NODES = {
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Num,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.USub,
    ast.UAdd,
    ast.FloorDiv,
    ast.Load,
    ast.Constant,
}

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

class CalculatorTool:
    name = "calculator"
    description = "安全的 +, -, *, /, %, ** 计算工具"

    async def arun(self, tool_input: ToolInput) -> ToolOutput:
        expression = tool_input.context.get("expression") or tool_input.task
        try:
            value = _evaluate(expression)
            return ToolOutput(
                content=f"{expression} = {value}",
                metadata={"expression": expression, "value": value},
            )
        except Exception as exc:
            return ToolOutput(
                content=f"计算失败: {exc}",
                metadata={"expression": expression, "error": str(exc)},
            )

def _evaluate(expression: str):
    node = ast.parse(expression, mode="eval")
    for sub in ast.walk(node):
        if type(sub) not in _ALLOWED_NODES:
            raise ValueError(f"不支持的语法: {type(sub).__name__}")
    return _eval_node(node.body)

def _eval_node(node):
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        op_type = type(node.op)
        if op_type not in _OPERATORS:
            raise ValueError(f"不支持的运算: {op_type.__name__}")
        return _OPERATORS[op_type](left, right)
    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise ValueError("不支持的单目运算")
    raise ValueError(f"不支持的节点: {type(node).__name__}")
