from __future__ import annotations

import pytest

from online_acceptance import OnlineAcceptanceError, validate_path_a_evidence


def valid_evidence():
    return {
        "path": "A",
        "status": "passed",
        "conversation_id": "conv-1",
        "interaction_id": "int-1",
        "toolbox": {
            "box_name": "供应链计算函数工具箱",
            "box_id": "current-box",
            "status": "published",
            "enabled_tool_count": 13,
        },
        "queries": [
            {
                "dataset": "forecast",
                "condition": {"field": "id", "operator": "eq", "value": "F1"},
                "rows": [{"id": "F1", "qty": 3000}],
                "bkn_receipt": {
                    "receipt_id": "receipt-1",
                    "dataset": "forecast",
                    "interaction_id": "int-1",
                    "row_count": 1,
                },
            }
        ],
        "tool_call": {"status_code": 200, "operation_id": "backward_plan"},
        "trace": {"reread": True, "conversation_id": "conv-1", "interaction_id": "int-1"},
    }


def test_accepts_real_mcp_to_toolbox_trace_evidence():
    result = validate_path_a_evidence(valid_evidence())
    assert result["status"] == "passed"


def test_blocks_unfiltered_context_loader_result():
    evidence = valid_evidence()
    evidence["queries"][0]["rows"].append({"id": "F2", "qty": 99})
    with pytest.raises(OnlineAcceptanceError, match="condition"):
        validate_path_a_evidence(evidence)


def test_blocks_missing_or_mismatched_receipt():
    evidence = valid_evidence()
    evidence["queries"][0]["bkn_receipt"].pop("receipt_id")
    with pytest.raises(OnlineAcceptanceError, match="receipt"):
        validate_path_a_evidence(evidence)


def test_blocks_offline_substitution_even_when_answer_exists():
    evidence = valid_evidence()
    evidence["status"] = "offline_passed"
    evidence["offline_fallback"] = True
    with pytest.raises(OnlineAcceptanceError, match="blocked"):
        validate_path_a_evidence(evidence)
