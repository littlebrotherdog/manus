"""Local implementation of multi-purpose function tools."""

from __future__ import annotations

import asyncio
import io
import json
import math
import random
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .base import FunctionTool, ToolInput, ToolOutput, ToolRegistry
from .local_search import LocalSearchTool

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SEED_DOCS_TOOL = LocalSearchTool()
_GLOBAL_MEMORY: list[dict[str, Any]] = []

@dataclass
class ToolSpec:
    name: str
    description: str
    handler: Any

async def _tool_get_temperature(tool_input: ToolInput) -> ToolOutput:
    city = (tool_input.context.get("city") or tool_input.task or "未知地点").strip()
    base = sum(ord(c) for c in city) or 42
    temp_c = round(10 + (base % 15) + 0.1 * (base % 5), 1)
    wind_kmh = round(5 + (base % 20) * 0.7, 1)
    content = f"{city} 当前温度 {temp_c}°C，风速 {wind_kmh} km/h"
    return ToolOutput(content=content, metadata={"city": city, "temperature_c": temp_c, "wind_kmh": wind_kmh})

async def _tool_generate_image(tool_input: ToolInput) -> ToolOutput:
    prompt = tool_input.context.get("prompt") or tool_input.task
    seed = abs(hash(prompt)) % (10**8)
    url = f"fake-image://{seed}"
    return ToolOutput(content=f"已根据提示生成图像(预览ID {seed})", metadata={"prompt": prompt, "image_url": url})

async def _tool_web_search(tool_input: ToolInput) -> ToolOutput:
    query = tool_input.context.get("query") or tool_input.task
    top_k = int(tool_input.context.get("top_k", 3))
    result = await _SEED_DOCS_TOOL.arun(ToolInput(task=query, context={}))
    payload = result.metadata.get("results", [])[:top_k]
    return ToolOutput(content=result.content, metadata={"results": payload, "query": query})

async def _tool_open_url(tool_input: ToolInput) -> ToolOutput:
    url = tool_input.context.get("url") or tool_input.task
    content = f"已打开 {url}，标题：{Path(url).name or '未知'}"
    return ToolOutput(content=content, metadata={"url": url})

async def _tool_youtube_summary(tool_input: ToolInput) -> ToolOutput:
    video_id = tool_input.context.get("video_id") or tool_input.context.get("url") or tool_input.task
    summary = f"视频 {video_id} 的关键要点：1) 开场介绍 2) 核心论点 3) 结论"
    return ToolOutput(content=summary, metadata={"video": video_id})

async def _tool_google_scholar(tool_input: ToolInput) -> ToolOutput:
    query = tool_input.context.get("query") or tool_input.task
    papers = [
        {"title": f"{query} - 一项系统研究", "year": 2024, "authors": ["Doe", "Li"]},
        {"title": f"关于 {query} 的最新进展", "year": 2023, "authors": ["Wang"]},
    ]
    content = "\n".join(f"- {p['title']} ({p['year']})" for p in papers)
    return ToolOutput(content=content, metadata={"query": query, "papers": papers})

async def _tool_parse_file(tool_input: ToolInput) -> ToolOutput:
    path = (tool_input.context.get("path") or tool_input.task).strip()
    max_chars = int(tool_input.context.get("max_chars", 400))
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = (_PROJECT_ROOT / candidate).resolve()
    if not str(candidate).startswith(str(_PROJECT_ROOT)):
        raise ValueError("越界访问")
    if not candidate.exists():
        raise FileNotFoundError(f"文件不存在: {candidate}")
    text = candidate.read_text(encoding="utf-8")[:max_chars]
    return ToolOutput(content=text, metadata={"path": str(candidate), "length": len(text)})

async def _tool_python(tool_input: ToolInput) -> ToolOutput:
    code = tool_input.context.get("code") or tool_input.task
    local_vars: dict[str, Any] = {}
    stdout = io.StringIO()
    env = {"__builtins__": {"print": print, "range": range, "len": len, "sum": sum, "min": min, "max": max}, "math": math}
    try:
        with redirect_stdout(stdout):
            exec(code, env, local_vars)
    except Exception as exc:  # pragma: no cover - runtime errors tested via metadata
        return ToolOutput(content=f"执行失败: {exc}", metadata={"error": str(exc)})
    output = stdout.getvalue().strip()
    result = local_vars.get("result")
    metadata = {"stdout": output, "result": result}
    return ToolOutput(content=output or str(result) or "执行完成", metadata=metadata)

async def _tool_qwen_search(tool_input: ToolInput) -> ToolOutput:
    return await _tool_web_search(tool_input)

async def _tool_batch_search(tool_input: ToolInput) -> ToolOutput:
    queries = tool_input.context.get("queries")
    if not isinstance(queries, Iterable):
        queries = [tool_input.task]
    aggregated = {}
    for q in queries:
        res = await _SEED_DOCS_TOOL.arun(ToolInput(task=str(q), context={}))
        aggregated[str(q)] = res.metadata.get("results", [])
    return ToolOutput(content=f"已完成 {len(aggregated)} 个查询", metadata={"results": aggregated})

async def _tool_memory(tool_input: ToolInput) -> ToolOutput:
    entry = {"task": tool_input.task, **tool_input.context}
    _GLOBAL_MEMORY.append(entry)
    return ToolOutput(content="记忆已保存", metadata={"size": len(_GLOBAL_MEMORY)})

async def _tool_think(tool_input: ToolInput) -> ToolOutput:
    return ToolOutput(content=f"思考: {tool_input.task}", metadata={})

async def _tool_plan(tool_input: ToolInput) -> ToolOutput:
    steps = tool_input.context.get("steps") or [tool_input.task]
    lines = "\n".join(f"{idx+1}. {step}" for idx, step in enumerate(steps))
    return ToolOutput(content=lines, metadata={"steps": steps})

async def _tool_final_answer(tool_input: ToolInput) -> ToolOutput:
    return ToolOutput(content=tool_input.task, metadata={})

_TOOLS = [
    ToolSpec("get_temperature_and_windspeed", "查询指定城市的温度与风速", _tool_get_temperature),
    ToolSpec("generate_image", "根据提示生成示意图片", _tool_generate_image),
    ToolSpec("web_search", "检索本地知识库", _tool_web_search),
    ToolSpec("open_url", "打开链接并返回标题", _tool_open_url),
    ToolSpec("get_youtube_video_summary", "总结 YouTube 视频", _tool_youtube_summary),
    ToolSpec("google_scholar", "返回示例学术结果", _tool_google_scholar),
    ToolSpec("parse_file", "读取仓库文件", _tool_parse_file),
    ToolSpec("execute_python", "执行 Python 代码", _tool_python),
    ToolSpec("python", "执行 Python 代码", _tool_python),
    ToolSpec("PythonInterpreter", "执行 Python 代码", _tool_python),
    ToolSpec("execute_python_qwen3", "执行 Python 代码", _tool_python),
    ToolSpec("search", "Qwen 搜索接口", _tool_qwen_search),
    ToolSpec("batch_search", "批量搜索", _tool_batch_search),
    ToolSpec("memory", "写入长期记忆", _tool_memory),
    ToolSpec("think", "记录思考", _tool_think),
    ToolSpec("create_plan", "创建计划", _tool_plan),
    ToolSpec("update_plan", "更新计划", _tool_plan),
    ToolSpec("final_answer", "返回最终答案", _tool_final_answer),
]


def register_functools_tools(registry: ToolRegistry) -> ToolRegistry:
    for spec in _TOOLS:
        registry.register(FunctionTool(name=spec.name, description=spec.description, func=spec.handler))
    return registry
