"""Docs/Skill contract: Agent queries Context Loader and inlines resolved_context."""

from __future__ import annotations

import json
from pathlib import Path

PACK = Path(__file__).resolve().parents[2]
HANDOFF = PACK / "docs" / "第三方Agent数据交接说明.md"
CONTRACT = PACK / "docs" / "payloads" / "resolved-context-contracts.json"
SKILLS = [
    PACK / "skills" / "production-schedule-backward-planning" / "SKILL.md",
    PACK / "skills" / "demand-fulfillment-capacity-analysis" / "SKILL.md",
    PACK / "skills" / "demand-fulfillment-requirement-coverage-analysis" / "SKILL.md",
]

PROTOCOL_SNIPPETS = [
    "官方 Context Loader",
    "bkn_start_interaction",
    "bkn_receipt",
    "只查询一次",
    "resolved_context",
    "函数服务不查询",
    "bkn_finish_interaction",
    "禁止伪造",
    "禁止 CSV",
]


def test_handoff_document_exists_and_states_protocol():
    text = HANDOFF.read_text(encoding="utf-8")
    for snippet in PROTOCOL_SNIPPETS:
        assert snippet in text, f"交接说明缺少：{snippet}"


def test_skills_state_the_same_handoff_protocol():
    for path in SKILLS:
        text = path.read_text(encoding="utf-8")
        for snippet in PROTOCOL_SNIPPETS:
            assert snippet in text, f"{path} 缺少：{snippet}"


def test_handoff_lists_operation_datasets_from_contract():
    text = HANDOFF.read_text(encoding="utf-8")
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    for name, spec in payload["operations"].items():
        assert name in text, f"交接说明未列出 operation {name}"
        for dataset in spec["required_rows"]:
            assert dataset in text, f"交接说明未列出数据集 {dataset}"


def test_handoff_forbids_wrapping_context_loader():
    text = HANDOFF.read_text(encoding="utf-8")
    assert "不要封装 Context Loader" in text
    assert "ContextLoaderClient" not in text
    assert "httpx" not in text
    assert "MCP Client" not in text


def test_handoff_example_is_total_sellable_and_has_no_secret():
    text = HANDOFF.read_text(encoding="utf-8")
    assert "total_sellable" in text
    assert "bkn_start_interaction" in text
    assert "bak_" not in text
    assert "sk-" not in text
