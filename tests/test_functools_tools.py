import asyncio

import pytest

from manus.tools import ToolInput, build_default_registry


def _run(tool_name: str, task: str = "", context: dict | None = None):
    registry = build_default_registry()
    tool = registry.get(tool_name)
    return asyncio.run(tool.arun(ToolInput(task=task, context=context or {})))


def test_weather_tool_returns_metadata():
    output = _run("get_temperature_and_windspeed", context={"city": "上海"})
    assert "上海" in output.content
    assert "temperature_c" in output.metadata


def test_parse_file_reads_repo_file(tmp_path):
    # 写入临时文件并确保 parse_file 只能读取仓库根目录下的内容
    readme_output = _run("parse_file", context={"path": "README.md", "max_chars": 50})
    assert "Manus" in readme_output.content

    outside_file = tmp_path / "secret.txt"
    outside_file.write_text("should not read", encoding="utf-8")
    with pytest.raises((ValueError, FileNotFoundError)):
        _run("parse_file", context={"path": str(outside_file)})


def test_execute_python_returns_stdout_and_result():
    code = "result = 3 * 7\nprint('value', result)"
    output = _run("execute_python", task=code)
    assert output.metadata["result"] == 21
    assert "value 21" in output.content


def test_qwen_search_alias_uses_local_index():
    output = _run("qwen_search", task="FlowToolcallAgent")
    assert output.metadata["results"]
