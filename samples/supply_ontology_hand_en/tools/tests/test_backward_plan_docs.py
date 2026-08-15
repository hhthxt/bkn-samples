"""S1 and partner-handoff contracts for backward_plan."""

from __future__ import annotations

import json
from pathlib import Path

PACK = Path(__file__).resolve().parents[2]
HANDOFF = PACK / "docs" / "第三方Agent数据交接说明.md"
CONTRACT = PACK / "docs" / "payloads" / "resolved-context-contracts.json"
S1 = PACK / "skills" / "production-schedule-backward-planning" / "SKILL.md"
IO = PACK / "skills" / "production-schedule-backward-planning" / "references" / "io-contract.md"
RULES = PACK / "skills" / "production-schedule-backward-planning" / "references" / "business-rules.md"
REPORT = PACK / "skills" / "production-schedule-backward-planning" / "references" / "report-spec.md"

S1_SNIPPETS = [
    "官方 Context Loader",
    "bkn_start_interaction",
    "bkn_receipt",
    "只查询一次",
    "resolved_context",
    "函数服务不查询",
    "bkn_finish_interaction",
    "生产计划齐套倒排",
    "backward_plan",
    "一张需求预测",
    "禁止伪造",
    "禁止 CSV",
    "人工确认",
    "采购申请决策",
    "不创建 ERP",
]


def test_s1_skill_prefers_backward_plan_and_handoff_protocol():
    text = S1.read_text(encoding="utf-8")
    for snippet in S1_SNIPPETS:
        assert snippet in text, f"S1 SKILL 缺少：{snippet}"
    assert "不在 Skill 内重写公式" in text or "不在 Skill 中重写" in text
    assert "initiate_po" in text
    assert "无截止日" in text or "无日期" in text
    assert "替代" in text


def test_s1_references_keep_single_forecast_monitor_and_no_erp_write():
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in (IO, RULES, REPORT)
    )
    assert "backward_plan" in combined
    assert "一张" in combined and "预测" in combined
    assert "create_monitor_task" in combined
    assert "initiate_po" in combined or "ERP PR" in combined or "不创建 ERP" in combined


def test_handoff_lists_backward_plan_datasets():
    text = HANDOFF.read_text(encoding="utf-8")
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    required = payload["operations"]["backward_plan"]["required_rows"]
    assert "backward_plan" in text
    for dataset in required:
        assert dataset in text
    assert "不要封装 Context Loader" in text
    assert "生产计划齐套倒排" in text
