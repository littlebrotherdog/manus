"""Streamlit demo with streaming event visualization."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import List

import streamlit as st

from manus.agents.flows import AgentEvent
from manus.agents.orchestrator import ManusAgent
from manus.config import LLMConfig, ManusSettings
from manus.llm import HttpLLMClient
from manus.memory import MemoryStore
from manus.tools import build_default_registry

st.set_page_config(page_title="Manus Demo", page_icon="📜", layout="wide")
st.title("Manus 流式可视化 Demo")
st.caption("流式展示计划、工具输出与最终回答。")

if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.header("运行参数")
    default_model = st.text_input("模型 ID", value=LLMConfig().model)
    max_steps = st.slider("最大步骤", min_value=1, max_value=6, value=3)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, step=0.05)
    st.divider()
    st.markdown("**环境变量**: MANUS_LLM_API_KEY / MANUS_LLM_BASE_URL 可覆盖默认值。")

task = st.text_area("任务输入", value="列出 Manus 的关键组件", height=120)
run_button = st.button("运行 Manus", type="primary")

plan_box = st.container()
events_box = st.container()
final_box = st.container()
status_placeholder = st.empty()

async def _run(task_text: str):
    settings = ManusSettings()
    settings.llm.model = default_model
    settings.llm.temperature = temperature
    settings.max_steps = max_steps
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

    event_log: List[str] = []

    def on_event(event: AgentEvent):
        if event.type == "plan":
            steps = event.payload.get("steps", [])
            markdown = "\n".join(
                [f"{idx+1}. {step.get('instruction', '')}" for idx, step in enumerate(steps)]
            )
            plan_box.subheader("计划")
            plan_box.markdown(markdown or event.payload.get("raw", "(空)"))
        elif event.type == "tool":
            result = event.payload.get("output", {})
            summary = f"[{datetime.now().strftime('%H:%M:%S')}] {event.message}\n```"
            summary += f"{result.get('content', '')}"
            summary += "```"
            event_log.append(summary)
            events_box.subheader("实时工具输出")
            events_box.markdown("\n\n".join(event_log))
        elif event.type == "final":
            final_box.subheader("最终回答")
            final_box.success(event.payload.get("answer", ""))

    result = await agent.arun(task_text, event_callback=on_event)
    st.session_state.history.append(
        {
            "task": task_text,
            "answer": result["answer"],
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

if run_button and task.strip():
    status_placeholder.info("运行中……")
    try:
        asyncio.run(_run(task.strip()))
        status_placeholder.success("执行完成")
    except Exception as exc:  # pragma: no cover - UI feedback only
        status_placeholder.error(f"运行出错: {exc}")
else:
    st.info("输入任务并点击运行即可开始。")

if st.session_state.history:
    st.divider()
    st.subheader("运行历史")
    for item in reversed(st.session_state.history[-5:]):
        st.markdown(f"**{item['timestamp']}**: {item['task']}\n> {item['answer']}")
