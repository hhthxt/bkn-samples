"""S1 delivery scenario routing and partner-handoff coverage."""

from __future__ import annotations

from pathlib import Path

PACK = Path(__file__).resolve().parents[2]
HANDOFF = PACK / "docs" / "第三方Agent数据交接说明.md"
S1 = PACK / "skills" / "production-schedule-backward-planning" / "SKILL.md"
IO = PACK / "skills" / "production-schedule-backward-planning" / "references" / "io-contract.md"
RULES = PACK / "skills" / "production-schedule-backward-planning" / "references" / "business-rules.md"
REPORT = PACK / "skills" / "production-schedule-backward-planning" / "references" / "report-spec.md"
METRICS = PACK / "skills" / "production-schedule-backward-planning" / "references" / "kn-metrics.md"

S1_NAVIGATION_SNIPPETS = [
    "业务场景",
    "优先指标",
    "优先函数",
    "生产计划齐套倒排",
    "新增客户需求",
    "business_date",
    "2026-08-25",
    "人工确认",
    "采购申请决策",
    "不创建 ERP",
]


def test_s1_skill_routes_delivery_scenarios_without_runtime_rebuild():
    text = S1.read_text(encoding="utf-8")
    for snippet in S1_NAVIGATION_SNIPPETS:
        assert snippet in text, f"S1 SKILL 缺少：{snippet}"
    for obsolete in ("run_code", "read_skill_file", "runtime/supply_fn", "build_snapshot"):
        assert obsolete not in text
    assert "resolved_context" not in text
    assert "resolved_context_compressed" not in text
    assert "supply_chain_compute" not in text
    assert "函数服务不查询" not in text


def test_s1_references_keep_single_forecast_monitor_and_no_erp_write():
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in (IO, RULES, REPORT)
    )
    assert "backward_plan" in combined
    assert "一张" in combined and "预测" in combined
    assert "create_monitor_task" in combined
    assert "initiate_po" in combined or "ERP PR" in combined or "不创建 ERP" in combined


def test_s1_is_self_contained_and_maps_user_input_to_function_contract():
    skill = S1.read_text(encoding="utf-8")
    io_contract = IO.read_text(encoding="utf-8")
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (S1, IO, RULES, REPORT, METRICS)
    )

    assert "product_query" in combined
    assert "生产计划齐套倒排" in io_contract
    assert "business_date" in skill
    assert "2026-08-25" in io_contract
    assert "resolved_context" not in combined
    assert "supply_chain_compute" not in combined
    assert "71600d21-c9f6-4336-bfbf-95bfb3654674" not in skill
    assert "docs/" not in combined


def test_handoff_exposes_backward_plan_as_a_business_function():
    text = HANDOFF.read_text(encoding="utf-8")
    assert "生产计划齐套倒排" in text
    assert "函数自行读取" in text
    assert "不要自行封装 Context Loader" in text
    assert "数据快照或 `resolved_context` 作为函数参数传递" in text
