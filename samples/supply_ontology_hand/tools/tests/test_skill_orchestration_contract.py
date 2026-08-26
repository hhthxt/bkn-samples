from __future__ import annotations

import pytest

from skill_orchestration import build_toolbox_request


REQUIRED = (
    "forecast",
    "bom",
    "material",
    "inventory",
    "purchase_order",
    "purchase_request",
    "mrp",
)


def valid_request():
    return {
        "bkn_context": {
            "conversation_id": "conv_test",
            "interaction_id": "int_test",
        },
        "resolved_context": {
            "source": "openbkn_context_loader",
            "rows": {name: [{"snapshot": name}] for name in REQUIRED},
            "receipts": {name: {"receipt_id": f"receipt-{name}"} for name in REQUIRED},
        },
        "parameters": {
            "product_query": "U00-000080",
            "forecast_id": "0000023181-FUTURE",
            "demand_end": "2026-10-31",
            "demand_qty": 3000,
            "substitute_enabled": False,
        },
    }


def test_builds_agent_managed_toolbox_request_without_persistence():
    request = valid_request()
    result = build_toolbox_request("backward_plan", **request)

    assert result["execution_mode"] == "agent_orchestrated"
    assert result["bkn_context"] == request["bkn_context"]
    assert result["resolved_context"] == request["resolved_context"]
    assert result["arguments"] == request["parameters"]


@pytest.mark.parametrize("missing", ["conversation_id", "interaction_id"])
def test_requires_agent_trace_ids(missing):
    request = valid_request()
    request["bkn_context"].pop(missing)
    with pytest.raises(ValueError, match=missing):
        build_toolbox_request("backward_plan", **request)


def test_requires_receipts_for_every_required_dataset():
    request = valid_request()
    request["resolved_context"]["receipts"].pop("mrp")
    with pytest.raises(ValueError, match="mrp"):
        build_toolbox_request("backward_plan", **request)


def test_requires_online_context_loader_source():
    request = valid_request()
    request["resolved_context"]["source"] = "offline_test"
    with pytest.raises(ValueError, match="openbkn_context_loader"):
        build_toolbox_request("backward_plan", **request)


def test_requires_receipt_id_for_every_required_dataset():
    request = valid_request()
    request["resolved_context"]["receipts"]["forecast"] = {"dataset": "forecast"}
    with pytest.raises(ValueError, match="forecast"):
        build_toolbox_request("backward_plan", **request)


def test_rejects_incomplete_business_parameters_before_function_call():
    request = valid_request()
    request["parameters"].pop("demand_end")
    with pytest.raises(ValueError, match="demand_end"):
        build_toolbox_request("backward_plan", **request)


def test_does_not_allow_substitution_policy_to_be_implicit():
    request = valid_request()
    request["parameters"].pop("substitute_enabled")
    with pytest.raises(ValueError, match="substitute_enabled"):
        build_toolbox_request("backward_plan", **request)
