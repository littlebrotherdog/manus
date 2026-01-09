# Manus

Manus 是一个极简的「规划 + 工具 + LLM」执行内核，用于快速验证多工具智能体的想法。它摒弃笨重依赖，只保留最关键的运行路径：

- 统一的 LLM 访问层：默认连接 `https://api.siliconflow.cn/v1`，开箱即用。
- 可插拔的工具注册中心：几行代码即可添加自定义工具或外部 API。
- 轻量记忆体：捕获工具输出，供后续总结与评价。
- 规划编排器：将任务拆解为步骤，逐步调用工具再由模型收敛答案。
- Typer CLI：`manus chat --task "..."` 即可体验端到端流程。

> Manus 定位为「实验底座」，适合搭建原型、教学示例或快速孵化新 Agent 能力。

## 核心能力

1. **LLM 抽象**：`manus.llm.HttpLLMClient` 基于 OpenAI-compatible 协议，包含超时、温度、最大 token 等常用参数，并支持环境变量覆盖 API Key。
2. **规划器**：`manus.agents.planning.PlanBuilder` 通过提示词生成 2-4 步执行计划，并解析 `[tool: xxx]` 标记以绑定工具。
3. **工具系统**：`ToolRegistry` 管理工具声明和 prompt 片段，目前内置 `search`（基于 `manus/data/seed_documents.json` 的本地检索）与 `calculator`（安全算式执行）。
4. **记忆与总结**：`MemoryStore` 记录每步工具结果，`ManusAgent` 会在结尾调用 LLM 将这些片段凝练成最终回答。
5. **事件流**：执行过程中会产出 `plan`、`tool`、`final` 等事件，可直接送入日志或 UI（例如 Streamlit demo）。

## 目录速览

```
manus/
├── README.md
├── pyproject.toml
├── manus/
│   ├── agents/
│   │   ├── flows.py
│   │   ├── orchestrator.py
│   │   └── planning.py
│   ├── cli.py
│   ├── config.py
│   ├── llm/
│   │   ├── base.py
│   │   └── http_client.py
│   ├── memory/
│   │   └── store.py
│   └── tools/
│       ├── base.py
│       ├── calculator.py
│       ├── local_search.py
│       └── __init__.py
├── docs/overview.md
├── manus/data/seed_documents.json
├── app/streamlit_app.py
└── tests/
    ├── conftest.py
    ├── test_local_search.py
    └── test_plan_parser.py
```

## 快速开始

```bash
cd /data/manus
uv venv && source .venv/bin/activate
uv pip install -e .
export MANUS_LLM_API_KEY="YOUR_API_KEY_FROM_CLOUD_SILICONFLOW_CN"  # 或根据需要替换
manus chat --task "列出 Manus 的关键组件"
```

> 项目在 `pyproject.toml` 中将 `tool.uv.link-mode` 设为 `copy`，可兼容跨磁盘/不同挂载点的环境，避免 `uv pip install` 提示硬链接失败；如需硬链接，可在命令行传入 `--link-mode=hardlink` 覆盖。

### Streamlit 可视化

```bash
streamlit run manus/app/streamlit_app.py
```

界面会实时输出计划、每一步工具内容与最终回答，并在侧栏调整模型、步数、temperature。

### 常用环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `MANUS_LLM_BASE_URL` | `https://api.siliconflow.cn/v1` | LLM 服务地址 |
| `MANUS_LLM_API_KEY` | `YOUR_API_KEY_FROM_CLOUD_SILICONFLOW_CN` | 认证 Token |
| `MANUS_MODEL` | `deepseek-ai/DeepSeek-V3.1` | 默认模型，也可在 CLI 使用 `--model` 覆盖 |

## CLI 用法

```
manus chat --task "需要完成的目标" --max-steps 4
```

- `--task / -t`：必填，描述目标。
- `--model`：覆盖默认模型 ID。
- `--max-steps`：限制执行的工具步数。

CLI 会依次打印计划、每步工具事件以及最终回答。

## 扩展工具

1. 编写实现 `Tool` 协议的类：
   ```python
   from manus.tools import Tool, ToolInput, ToolOutput

   class WeatherTool:
       name = "weather"
       description = "获取实时天气"

       async def arun(self, tool_input: ToolInput) -> ToolOutput:
           data = fetch_weather(tool_input.task)
           return ToolOutput(content=data["summary"], metadata=data)
   ```
2. 在自定义脚本中注册：
   ```python
   from manus.tools import build_default_registry

   registry = build_default_registry()
   registry.register(WeatherTool())
   ```
3. 将 registry 传入 `ManusAgent` 或在 CLI 中自定义入口。

## 测试与质量

- `pytest`：验证计划解析与本地检索行为。
- 建议在新增工具时补充对应单测，并将伪造文档放入 `manus/data/`（或改用 importlib.resources），避免依赖真实外部接口。

## 文档索引

- [docs/overview.md](docs/overview.md)：涵盖架构、流程、模块解读与二次开发建议。

欢迎在此基础上添加更多工具、UI，或将 Manus 嵌入现有产品。EOF
