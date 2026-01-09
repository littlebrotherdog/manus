# Manus 项目总览

本文介绍 Manus 的设计目标、核心模块、执行流程以及二次开发指南，帮助你快速将该项目用于原型或生产实验。

## 设计目标

1. **轻量**：仅依赖 httpx、pydantic、typer、rich 等基础库，方便在任何 Python 环境落地。
2. **可观测**：事件模型贯穿计划、工具执行和最终回答，便于日志采集或可视化。
3. **易扩展**：工具注册中心与配置系统拆分良好，引入新工具或模型无需重写主流程。
4. **默认安全**：LLM 默认走 `https://api.siliconflow.cn/v1`，Calculator 工具仅允许安全 AST 节点，避免执行任意代码。

## 模块分层

| 层级 | 目录 | 说明 |
| --- | --- | --- |
| 接口层 | `manus/cli.py` | Typer CLI，调用 Agent 并打印事件流。 |
| 配置层 | `manus/config.py` | `LLMConfig`、`ManusSettings`，集中管理 base_url、API Key、默认工具。 |
| LLM 层 | `manus/llm/` | `HttpLLMClient` 基于 OpenAI-compatible `/chat/completions` 接口。 |
| Agent 层 | `manus/agents/` | `PlanBuilder`、`ManusAgent`、数据类型（Plan、PlanStep、AgentEvent）。 |
| 工具层 | `manus/tools/` | `ToolRegistry` 与默认工具（LocalSearch、Calculator）。 |
| 记忆层 | `manus/memory/` | `MemoryStore` 记录工具输出，供总结阶段读取。 |
| 数据层 | `manus/data/seed_documents.json` | 本地检索数据，可替换为企业知识。 |
| 可视化 | `app/streamlit_app.py` | Streamlit demo，流式展示事件。 |
| 测试 | `tests/` | 覆盖计划解析与检索工具。 |

## 执行流程

1. **接收任务**：CLI 将 `--task` 与可选参数传给 `ManusAgent`。
2. **生成计划**：`PlanBuilder` 用系统提示 + 工具列表提示 LLM 输出 2-4 步任务分解，并解析 `[tool: name]` 标记。
3. **解析工具**：`ManusAgent` 根据计划或上下文自动选择工具。
4. **执行工具**：对于每个步骤，`ToolRegistry.get()` 返回对应实现，`Tool.arun()` 以异步方式执行。
5. **写入记忆**：每次工具输出被封装为 `MemoryEvent`，供最终总结引用。
6. **生成回答**：`_summarize` 使用最新的记忆片段调用 LLM，形成最终响应。
7. **事件输出**：整个过程中持续推送 AgentEvent，可用于日志、UI 或评测系统。

## 配置与部署建议

- **API Key 管理**：在 shell 中导出 `MANUS_LLM_API_KEY`，或写入 `.env` 并在外部加载，避免硬编码。
- **模型切换**：通过 `ManusSettings().llm.model` 或 CLI `--model` 切换不同模型。SiliconFlow 兼容多种模型 ID。
- **代理支持**：如需自定义代理，可在 `httpx.AsyncClient` 初始化时添加 `proxies`。建议在外部包装 HttpLLMClient 以保持核心库简洁。

## 工具开发指南

1. **实现协议**：继承 `Tool` Protocol（鸭子类型），实现 `name`、`description` 和 `async arun`。
2. **注册**：调用 `ToolRegistry.register()`。可以在 CLI 扩展入口或自定义脚本里注入。
3. **上下文格式**：`ToolInput` 包含 `task` 和 `context`（含原始任务、步骤号等），返回 `ToolOutput` 并附带结构化 `metadata` 便于记录。
4. **观测**：ManusAgent 会在 `events` 中记录工具输入输出，可接驳日志/监控/Streamlit。

## 记忆策略

- 默认仅保留最近 6 条工具事件，用于控制 prompt 长度。
- 如需更丰富的记忆，可替换 `MemoryStore` 实现（例如 Redis、向量存储）并传入自定义对象。

## 测试策略

- `tests/test_plan_parser.py` 确保 `[tool: ...]` 标记解析正确。
- `tests/test_local_search.py` 校验本地检索结果结构。
- 建议在新增工具时仿照上述文件创建对应测试，并引入 `pytest` fixture 提供假数据。

## 路线图

1. **工具包**：新增 WebSearch/HTTP/Filesystem 等标准工具。
2. **多模型支持**：在 `LLMConfig` 中增加多路模型或路由逻辑。
3. **可视化**：提供 Streamlit 或 CLI TUI，用事件流驱动展示。
4. **评测**：集成基准测试脚本，自动验证多任务表现。

通过以上架构，Manus 能在保持简洁的同时，支撑从 Demo 到小型生产实验的各类场景。EOF
