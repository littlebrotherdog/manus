"""Planning helpers for Manus."""

from __future__ import annotations

import re
from typing import List

from ..config import ManusSettings
from ..llm import ChatMessage, LLMClient
from ..memory import MemoryStore
from ..tools import ToolRegistry
from .flows import Plan, PlanStep

_PLAN_PROMPT = """
You are a planning module for a research agent. Produce a concise ordered list
of steps to solve the given task. Use 2-4 steps. Whenever a step requires tools,
annotate it in the format `[tool: TOOL_NAME]` where TOOL_NAME is from the tool list.
Respond using plain text bullet points.
""".strip()

_STEP_PATTERN = re.compile(r"^(?:[-*]?\s*)?(?:step\s*)?(\d+)[\).:-]?\s*(.+)$", re.I)
_TOOL_PATTERN = re.compile(r"\[tool\s*:?\s*([\w-]+)\]", re.I)

class PlanBuilder:
    def __init__(self, *, llm_client: LLMClient, settings: ManusSettings):
        self.llm = llm_client
        self.settings = settings

    async def build(self, task: str, memory: MemoryStore, registry: ToolRegistry) -> Plan:
        messages = [
            ChatMessage(role="system", content=_PLAN_PROMPT + "\n工具列表:\n" + registry.as_prompt_block()),
            ChatMessage(role="user", content=f"任务: {task}"),
        ]
        result = await self.llm.chat(
            messages,
            temperature=min(0.5, self.settings.llm.temperature + 0.2),
            max_tokens=512,
            model=self.settings.llm.model,
        )
        raw_text = result.content.strip()
        steps = _parse_plan(raw_text or task)
        if not steps:
            steps = [PlanStep(index=1, instruction=task)]
        return Plan(task=task, steps=steps, raw_text=raw_text)

def _parse_plan(text: str) -> List[PlanStep]:
    steps: List[PlanStep] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = _STEP_PATTERN.match(line)
        if match:
            _, content = match.groups()
        else:
            content = line
        tool = None
        tool_match = _TOOL_PATTERN.search(content)
        if tool_match:
            tool = tool_match.group(1).strip().lower()
            content = _TOOL_PATTERN.sub("", content).strip()
        steps.append(PlanStep(index=len(steps) + 1, instruction=content, suggested_tool=tool))
    return steps
