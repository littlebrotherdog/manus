"""High-level Manus agent orchestration."""

from __future__ import annotations

from typing import Callable, List

from ..config import ManusSettings
from ..llm import ChatMessage, LLMClient
from ..memory import MemoryStore
from ..tools import ToolInput, ToolRegistry, build_default_registry
from .flows import AgentEvent, Plan
from .planning import PlanBuilder

class ManusAgent:
    def __init__(
        self,
        *,
        settings: ManusSettings,
        llm_client: LLMClient,
        tool_registry: ToolRegistry | None = None,
        memory: MemoryStore | None = None,
        planner: PlanBuilder | None = None,
    ):
        self.settings = settings
        self.llm = llm_client
        self.memory = memory or MemoryStore()
        self.tool_registry = tool_registry or build_default_registry()
        self.planner = planner or PlanBuilder(llm_client=llm_client, settings=settings)

    async def arun(
        self,
        task: str,
        *,
        max_steps: int | None = None,
        event_callback: Callable[[AgentEvent], None] | None = None,
    ) -> dict:
        events: List[AgentEvent] = []

        def emit(event: AgentEvent):
            events.append(event)
            if event_callback:
                event_callback(event)

        plan: Plan = await self.planner.build(task, self.memory, self.tool_registry)
        emit(
            AgentEvent(
                type="plan",
                message="生成计划",
                payload={"raw": plan.raw_text, "steps": [s.__dict__ for s in plan.steps]},
            )
        )
        limit = max_steps or self.settings.max_steps
        for step in plan.steps[:limit]:
            tool_name = self._resolve_tool(step.instruction, step.suggested_tool)
            tool = self.tool_registry.get(tool_name)
            tool_input = ToolInput(
                task=step.instruction,
                context={"original_task": task, "step": step.index},
            )
            result = await tool.arun(tool_input)
            self.memory.add(
                role="tool",
                content=f"{tool.name}: {result.content}",
                metadata={"tool": tool.name, **result.metadata},
            )
            emit(
                AgentEvent(
                    type="tool",
                    message=f"Step {step.index}: {tool.name}",
                    payload={
                        "input": {"task": tool_input.task, "context": tool_input.context},
                        "output": {"content": result.content, "metadata": result.metadata},
                    },
                )
            )
        answer = await self._summarize(task)
        emit(AgentEvent(type="final", message="答案", payload={"answer": answer}))
        return {
            "task": task,
            "plan": plan,
            "events": events,
            "answer": answer,
        }

    async def _summarize(self, task: str) -> str:
        history = self.memory.tail(6)
        user_context = "\n".join(event.content for event in history)
        messages = [
            ChatMessage(
                role="system",
                content="你是 Manus，负责把工具执行内容整理成结构化回答。",
            ),
            ChatMessage(
                role="assistant",
                content=f"工具上下文:\n{user_context}",
            ),
            ChatMessage(role="user", content=f"请基于上述记录完成任务: {task}"),
        ]
        completion = await self.llm.chat(
            messages,
            temperature=max(0.1, self.settings.llm.temperature - 0.1),
            max_tokens=self.settings.llm.max_tokens,
            model=self.settings.llm.model,
        )
        return completion.content.strip()

    def _resolve_tool(self, instruction: str, suggested: str | None) -> str:
        candidates = [suggested] if suggested else []
        text = instruction.lower()
        if "calc" in text or "计算" in text or any(char.isdigit() for char in instruction):
            candidates.append("calculator")
        candidates.append("search")
        for name in candidates:
            if not name:
                continue
            try:
                self.tool_registry.get(name)
                return name
            except KeyError:
                continue
        return self.tool_registry.listed()[0]
