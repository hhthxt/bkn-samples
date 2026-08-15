"""CSV snapshot tests for KN function library (口径清单 §2)."""

from __future__ import annotations

import pytest

from fn import (
    CannotCompute,
    bom_list,
    bom_shared_list,
    kitting_net_demand,
    layered_inventory,
    leadtime_days,
    load_csv_snapshot,
    resolve_warehouse_scope,
    substitute_status,
    supply_status,
    theoretical_build,
    total_sellable,
)


@pytest.fixture(scope="module")
def snap():
    return load_csv_snapshot()


def test_warehouse_presets():
    prod = resolve_warehouse_scope("production_available")
    fg = resolve_warehouse_scope("finished_goods")
    assert len(prod) == 7
    assert "Suzhou Semi-finished Goods Warehouse" in prod
    assert "昆山成品仓" not in prod
    assert fg == [
        "Suzhou Finished Goods Warehouse",
        "Urumqi Finished Goods Warehouse",
        "Harbin Finished Goods Warehouse",
    ]
    assert resolve_warehouse_scope("all") == []


def test_bom_list_382_l1(snap):
    out = bom_list(snap, "382-000005", depth=1, include_substitute=False)
    assert out["l1_main_count"] == 9
    codes = [r["material_code"] for r in out["lines"]]
    assert codes == [
        "791-000013",
        "606-000989",
        "606-000990",
        "528-000036",
        "791-000007",
        "994-000550",
        "468-000493",
        "468-000530",
        "791-000015",
    ]
    assert "available_qty" not in out["lines"][0]


def test_bom_list_382_counts(snap):
    out = bom_list(snap, "382-000005", depth=None, include_substitute=False)
    assert out["rows_incl_root"] == 507
    assert out["line_count"] == 313
    assert out["unique_child_count"] == 272
    assert out["max_level"] == 5


def test_bom_list_missing_product(snap):
    with pytest.raises(CannotCompute):
        bom_list(snap, "")


def test_bom_shared_382_p61(snap):
    out = bom_shared_list(snap, ["382-000005", "P61-000351"], include_substitute=False)
    assert out["shared_count"] == 28
    assert "356-000081" in out["shared_codes"]


def test_bom_shared_three_products(snap):
    out = bom_shared_list(
        snap, ["382-000005", "P61-000351", "U00-000151"], include_substitute=False
    )
    assert out["shared_count"] == 11


def test_bom_shared_one_product(snap):
    with pytest.raises(CannotCompute):
        bom_shared_list(snap, ["382-000005"])


def test_substitute_status_382(snap):
    out = substitute_status(snap, "382-000005")
    assert out["has_alt_groups"] is True
    assert out["group_count"] == 70
    assert out["substitute_enabled"] == "unknown"


def test_leadtime(snap):
    assert leadtime_days(snap, "606-000989") == 14
    assert leadtime_days(snap, "382-000005") == 1
    assert leadtime_days(snap, "994-000550") == 35
    with pytest.raises(CannotCompute):
        leadtime_days(snap, "")


def test_theoretical_and_sellable_382_no_sub(snap):
    th = theoretical_build(snap, "382-000005", substitute_enabled=False)
    sell = total_sellable(snap, "382-000005", substitute_enabled=False)
    assert th["theoretical_build_qty"] == 0
    assert sell["fg_qty"] == pytest.approx(534, rel=0, abs=0.01)
    assert sell["total_sellable_qty"] == pytest.approx(534, rel=0, abs=0.01)
    assert "in_transit" not in sell or sell.get("include_in_transit") is False


def test_sellable_u00(snap):
    sell = total_sellable(snap, "U00-000151", substitute_enabled=False)
    assert sell["fg_qty"] == pytest.approx(3800, rel=0, abs=0.01)
    assert sell["total_sellable_qty"] >= sell["fg_qty"]


def test_kitting_382_50_not_s1(snap):
    out = kitting_net_demand(snap, "382-000005", qty=50, substitute_enabled=False)
    assert out["kitting_ok"] is False
    l1s = {g.get("l1_parent") for g in out["gaps"]} | {g["material_code"] for g in out["gaps"]}
    assert "791-000007" in l1s or "791-000015" in l1s
    assert "delay_a" not in out
    assert "supply_status" not in out


def test_supply_status_requires_due_date(snap):
    out = supply_status(snap, "791-000007", due_date=None, gross_requirement=50)
    assert out["status"] == "unknown"


def test_layered_inventory_382_l1(snap):
    out = layered_inventory(snap, "382-000005", depth=1)
    by_code = {r["material_code"]: r["available_qty"] for r in out["lines"]}
    assert by_code["791-000013"] == pytest.approx(1000, rel=0, abs=0.01)
    assert by_code["791-000007"] == pytest.approx(0, rel=0, abs=0.01)
    assert by_code["791-000015"] == pytest.approx(0, rel=0, abs=0.01)
    assert "reserved_qty" in out["lines"][0]
    assert len(out["warehouse_filter"]) == 7


def test_max_build_alias_equals_theoretical(snap):
    th = theoretical_build(snap, "382-000005", substitute_enabled=False)
    from fn import max_build_without_po

    mb = max_build_without_po(snap, "382-000005", substitute_enabled=False)
    assert mb["theoretical_build_qty"] == th["theoretical_build_qty"]
