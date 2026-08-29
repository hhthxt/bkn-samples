"""Docs/Skill contract for third-party handoff without legacy snapshots."""

from __future__ import annotations

from pathlib import Path

PACK = Path(__file__).resolve().parents[2]
HANDOFF = PACK / "docs" / "第三方Agent数据交接说明.md"
PROTOCOL_SNIPPETS = [
    "官方 Context Loader",
    "bkn_start_interaction",
    "bkn_finish_interaction",
    "不得以 CSV",
    "业务参数",
    "sandbox_sdk.bkn",
]


def test_handoff_document_exists_and_states_protocol():
    text = HANDOFF.read_text(encoding="utf-8")
    for snippet in PROTOCOL_SNIPPETS:
        assert snippet in text, f"交接说明缺少：{snippet}"


def test_s3_no_longer_depends_on_legacy_snapshot_protocol():
    path = PACK / "skills" / "demand-fulfillment-requirement-coverage-analysis" / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    assert "run_code" not in text
    assert "resolved_context" not in text
    assert "函数服务不查询" not in text


def test_handoff_keeps_bkn_data_loading_inside_the_function():
    text = HANDOFF.read_text(encoding="utf-8")
    assert "数据快照或 `resolved_context` 作为函数参数传递" in text
    assert "数据快照" in text
    assert "函数自行读取" in text


def test_handoff_forbids_wrapping_context_loader():
    text = HANDOFF.read_text(encoding="utf-8")
    assert "不要自行封装 Context Loader" in text
    assert "ContextLoaderClient" not in text
    assert "httpx" not in text
    assert "MCP Client" not in text


def test_handoff_example_is_total_sellable_and_has_no_secret():
    text = HANDOFF.read_text(encoding="utf-8")
    assert "合计可售" in text
    assert "bkn_start_interaction" in text
    assert '"product": "382-000005"' in text
    assert "bak_" not in text
    assert "sk-" not in text
