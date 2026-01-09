import asyncio

from manus.tools import ToolInput
from manus.tools.calculator import CalculatorTool


def run_tool(expression: str):
    tool = CalculatorTool()
    return asyncio.run(tool.arun(ToolInput(task=expression, context={})))


def test_calculator_extracts_expression_inside_sentence():
    output = run_tool("请计算 1+1")
    assert output.metadata["value"] == 2


def test_calculator_supports_multiplication_symbol():
    output = run_tool("3×4")
    assert output.metadata["value"] == 12
