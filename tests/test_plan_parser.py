from manus.agents.planning import _parse_plan


def test_parse_plan_extracts_tool_annotations():
    text = """
    1. 审阅资料 [tool: search]
    Step 2) 计算工作量 [tool: calculator]
    - 3) 汇总报告
    """.strip()

    steps = _parse_plan(text)

    assert len(steps) == 3
    assert steps[0].suggested_tool == "search"
    assert steps[1].suggested_tool == "calculator"
    assert steps[2].suggested_tool is None
    assert steps[2].instruction.startswith("汇总")
