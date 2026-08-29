"""Function operation data-requirement contracts (Stage A Task 2)."""

from __future__ import annotations

import pytest

from context.operation_contracts import (
    ALLOWED_DATASETS,
    OPERATION_CONTRACTS,
    required_datasets,
)

EXPECTED = {
    "bom_list": frozenset({"bom"}),
    "bom_shared_list": frozenset({"bom"}),
    "material_where_used": frozenset({"bom"}),
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


def test_all_fourteen_operations_are_covered():
    assert len(EXPECTED) == 14
    assert len(OPERATION_CONTRACTS) == 14
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
