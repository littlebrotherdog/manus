import asyncio

from manus.tools import ToolInput
from manus.tools.local_search import LocalSearchTool


def test_local_search_returns_scored_results():
    tool = LocalSearchTool()
    output = asyncio.run(tool.arun(ToolInput(task="FlowToolcallAgent", context={})))
    assert "FlowToolcallAgent" in output.content
    assert output.metadata["results"]
