"""CLI entry points for Manus."""

from __future__ import annotations

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from .agents.orchestrator import ManusAgent
from .config import ManusSettings
from .llm import HttpLLMClient
from .memory import MemoryStore
from .tools import build_default_registry

app = typer.Typer(help="Manus lightweight agent")
console = Console()

@app.callback()
def main():
    """Entry point for Manus CLI."""
    pass

@app.command()
def chat(
    task: str = typer.Option(..., "--task", "-t", help="待完成的任务"),
    model: Optional[str] = typer.Option(None, help="LLM 模型 ID"),
    max_steps: int = typer.Option(3, help="执行的最大步骤数"),
):
    settings = ManusSettings()
    if model:
        settings.llm.model = model
    settings.max_steps = max_steps
    asyncio.run(_run_chat(task, settings))

async def _run_chat(task: str, settings: ManusSettings) -> None:
    client = HttpLLMClient(
        base_url=settings.llm.base_url,
        api_key=settings.llm.api_key,
        timeout=settings.llm.timeout,
    )
    agent = ManusAgent(
        settings=settings,
        llm_client=client,
        tool_registry=build_default_registry(),
        memory=MemoryStore(),
    )
    console.rule("计划")
    result = await agent.arun(task)
    plan = result["plan"]
    for step in plan.steps:
        console.print(f"[bold]{step.index}. {step.instruction}[/bold] (tool={step.suggested_tool or 'auto'})")
    console.rule("执行事件")
    for event in result["events"]:
        console.print(f"[{event.type}] {event.message}")
    console.rule("回答")
    console.print(Panel(result["answer"], title="Manus", subtitle=task))

if __name__ == "__main__":  # pragma: no cover
    app()
