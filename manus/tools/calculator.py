"""Deterministic math helper."""

from __future__ import annotations

import ast
import operator
import re

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
        raw_expression = tool_input.context.get("expression") or tool_input.task
        expression = _sanitize_expression(raw_expression)
        try:
            value = _evaluate(expression)
            return ToolOutput(
                content=f"{expression} = {value}",
                metadata={"expression": expression, "value": value},
            )
        except SyntaxError as exc:
            return ToolOutput(
                content=f"计算失败: 表达式无法解析 ({exc})",
                metadata={"expression": raw_expression, "error": str(exc)},
            )
        except Exception as exc:
            return ToolOutput(
                content=f"计算失败: {exc}",
                metadata={"expression": raw_expression, "error": str(exc)},
            )


_SANITIZE_MAP = {
    "×": "*",
    "÷": "/",
    "^": "**",
}

_EXPRESSION_PATTERN = re.compile(r"[0-9\.\s\+\-\*/%\(\)]{2,}")
_ALLOWED_CHARS = set("0123456789.+-*/%() *")


def _sanitize_expression(expression: str) -> str:
    expr = expression.strip()
    expr = _strip_quotes(expr)
    for old, new in _SANITIZE_MAP.items():
        expr = expr.replace(old, new)
    if expr.endswith("="):
        expr = expr[:-1]
    if not _looks_like_math(expr):
        matches = _EXPRESSION_PATTERN.findall(expr)
        if matches:
            expr = matches[-1].strip()
    filtered = "".join(ch for ch in expr if ch in _ALLOWED_CHARS)
    if not filtered:
        raise SyntaxError("空表达式或不支持的字符")
    return filtered


def _looks_like_math(text: str) -> bool:
    return bool(re.fullmatch(r"[0-9\.\s\+\-\*/%\(\)\*]+", text))


def _strip_quotes(text: str) -> str:
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1].strip()
    return text


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
