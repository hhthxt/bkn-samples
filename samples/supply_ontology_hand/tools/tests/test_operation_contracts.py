"""Function operation data-requirement contracts (Stage A Task 2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.operation_contracts import (
    ALLOWED_DATASETS,
    OPERATION_CONTRACTS,
    required_datasets,
)

PACK = Path(__file__).resolve().parents[2]
CONTRACT_JSON = PACK / "docs" / "payloads" / "resolved-context-contracts.json"

EXPECTED = {
    "bom_list": frozenset({"bom"}),
    "bom_shared_list": frozenset({"bom"}),
    "layered_inventory": frozenset({"bom", "inventory"}),
    "substitute_status": frozenset({"bom", "inventory"}),
    "theoretical_build": frozenset({"bom", "inventory"}),
    "total_sellable": frozenset({"bom", "inventory"}),
    "kitting_net_demand": frozenset({"bom", "inventory", "purchase_order"}),
    "shared_contention": frozenset({"bom", "inventory", "purchase_order"}),
    "max_build_without_po": frozenset({"bom", "inventory"}),
    "leadtime_days": frozenset({"material"}),
    "supply_status": frozenset(
        {"material", "inventory", "purchase_order", "purchase_request", "mrp"}
    ),
    "open_forecast_count": frozenset({"forecast"}),
    "backward_plan": frozenset(
        {
            "forecast",
            "bom",
            "material",
            "inventory",
            "purchase_order",
            "purchase_request",
            "mrp",
        }
    ),
}


def test_all_thirteen_operations_are_covered():
    assert len(EXPECTED) == 13
    assert len(OPERATION_CONTRACTS) == 13
    assert set(OPERATION_CONTRACTS) == set(EXPECTED)
    for operation, datasets in EXPECTED.items():
        assert required_datasets(operation) == datasets


def test_backward_plan_requires_exactly_seven_datasets():
    datasets = required_datasets("backward_plan")
    assert datasets == frozenset(
        {
            "forecast",
            "bom",
            "material",
            "inventory",
            "purchase_order",
            "purchase_request",
            "mrp",
        }
    )
    assert "product" not in datasets


def test_contracts_only_use_allowed_logical_datasets():
    used = {name for datasets in OPERATION_CONTRACTS.values() for name in datasets}
    assert used <= ALLOWED_DATASETS


def test_unknown_operation_is_rejected():
    with pytest.raises(KeyError):
        required_datasets("unknown_op")


def test_missing_datasets_are_listed_exactly():
    present = {"bom"}
    missing = sorted(EXPECTED["kitting_net_demand"] - present)
    assert missing == ["inventory", "purchase_order"]


def test_json_contract_matches_python_definition():
    payload = json.loads(CONTRACT_JSON.read_text(encoding="utf-8"))
    json_ops = {
        name: frozenset(spec["required_rows"])
        for name, spec in payload["operations"].items()
    }
    assert len(json_ops) == 13
    assert json_ops == EXPECTED
    assert set(payload["allowed_datasets"]) == ALLOWED_DATASETS


def test_contracts_do_not_describe_context_loader_calls():
    payload = CONTRACT_JSON.read_text(encoding="utf-8")
    forbidden = (
        "query_object_instance",
        "run_sql",
        "query_metric",
        "bkn_start_interaction",
        "SELECT ",
        "mcp",
    )
    lowered = payload.lower()
    for token in forbidden:
        assert token.lower() not in lowered
