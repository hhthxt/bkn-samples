"""resolved_context 合同与 SnapshotEnvelope 组装测试（P0 设计 §3.2/§3.3/§5）。"""

from __future__ import annotations

import csv
import dataclasses
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import fn.snapshot as snapshot_module
from context.assembler import (
    DEFAULT_MAX_AGE_SECONDS,
    ResolvedContextAssembler,
    compute_input_digest,
)
from context.contract import (
    SOURCE_OFFLINE_TEST,
    SOURCE_OPENBKN,
    BknReceipt,
    ContextRequired,
    ContextStale,
    ReceiptRequired,
    ResolvedContext,
    SchemaMismatch,
    SnapshotEnvelope,
    SnapshotIncomplete,
)
from fn.snapshot import build_snapshot, load_csv_snapshot

KN_ID = "supply_ontology_hand"
NOW = datetime(2026, 8, 14, 13, 0, 0, tzinfo=timezone.utc)
REQUIRED = ("material", "bom", "inventory")


def _rows() -> dict[str, list[dict]]:
    return {
        "material": [
            {
                "material_code": "M1",
                "materialattr": "外购",
                "purchase_fixedleadtime": "14",
                "product_fixedleadtime": "",
            }
        ],
        "bom": [
            {
                "bom_material_code": "P1",
                "bom_level": "1",
                "material_code": "M1",
                "standard_usage": "2",
                "parent_material_code": "P1",
                "alt_group_no": "",
            }
        ],
        "inventory": [
            {
                "material_code": "M1",
                "warehouse": "苏州半成品仓",
                "available_base_qty": "100",
                "reserved_base_qty": "0",
            }
        ],
    }


def _receipts(datasets, interaction_id: str = "int_1") -> tuple[BknReceipt, ...]:
    return tuple(
        BknReceipt(
            dataset=name,
            interaction_id=interaction_id,
            resource_id=f"res_{name}",
            query_type="query_object_instance",
        )
        for name in datasets
    )


def _ctx(**overrides) -> ResolvedContext:
    payload = {
        "knowledge_network_id": KN_ID,
        "conversation_id": "conv_1",
        "interaction_id": "int_1",
        "captured_at": NOW,
        "rows": _rows(),
        "bkn_receipts": _receipts(REQUIRED),
    }
    payload.update(overrides)
    return ResolvedContext(**payload)


def _assembler(now: datetime = NOW, **kwargs) -> ResolvedContextAssembler:
    return ResolvedContextAssembler(now=lambda: now, **kwargs)


# --- 合同层 -------------------------------------------------------------


def test_resolved_context_requires_timezone_aware_captured_at():
    with pytest.raises(ContextRequired) as err:
        _ctx(captured_at=datetime(2026, 8, 14, 13, 0, 0))
    assert err.value.code == "context_required"
    assert "captured_at" in str(err.value)


def test_resolved_context_defensively_copies_rows():
    source = _rows()
    ctx = _ctx(rows=source)

    source["bom"].append({"material_code": "SNEAK"})
    source["material"][0]["material_code"] = "MUTATED"

    assert [r["material_code"] for r in ctx.rows["bom"]] == ["M1"]
    assert ctx.rows["material"][0]["material_code"] == "M1"


def test_resolved_context_rows_container_is_read_only():
    ctx = _ctx()
    with pytest.raises(TypeError):
        ctx.rows["bom"] = []
    with pytest.raises(dataclasses.FrozenInstanceError):
        ctx.interaction_id = "int_other"


def test_resolved_context_rejects_non_mapping_rows():
    with pytest.raises(SchemaMismatch) as err:
        _ctx(rows={"bom": ["not-a-row"]})
    assert err.value.code == "schema_mismatch"


def test_resolved_context_receipts_are_a_tuple():
    ctx = _ctx(bkn_receipts=list(_receipts(REQUIRED)))
    assert isinstance(ctx.bkn_receipts, tuple)
    assert ctx.bkn_receipts[0].dataset == "material"


def test_resolved_context_from_payload_parses_iso_and_receipts():
    ctx = ResolvedContext.from_payload(
        {
            "knowledge_network_id": KN_ID,
            "conversation_id": "conv_1",
            "interaction_id": "int_1",
            "captured_at": "2026-08-14T13:00:00Z",
            "bkn_receipts": [
                {
                    "dataset": "bom",
                    "interaction_id": "int_1",
                    "resource_id": "res_bom",
                }
            ],
            "rows": _rows(),
        }
    )
    assert ctx.captured_at == NOW
    assert ctx.captured_at.tzinfo is not None
    assert ctx.bkn_receipts == (
        BknReceipt(dataset="bom", interaction_id="int_1", resource_id="res_bom"),
    )
    assert ctx.rows["material"][0]["material_code"] == "M1"


def test_context_module_has_no_remote_client_code():
    pkg = Path(snapshot_module.__file__).resolve().parents[1] / "context"
    forbidden = ("requests", "httpx", "urllib", "socket", "mcp", "subprocess", "openbkn_client")
    for path in sorted(pkg.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert f"import {token}" not in text, f"{path.name} 引入了远程调用依赖 {token}"


# --- 组装：openbkn 校验 -------------------------------------------------


def test_assemble_openbkn_happy_path():
    envelope = _assembler().assemble(_ctx(), REQUIRED, source=SOURCE_OPENBKN)

    assert isinstance(envelope, SnapshotEnvelope)
    assert envelope.source == SOURCE_OPENBKN
    assert envelope.knowledge_network_id == KN_ID
    assert envelope.conversation_id == "conv_1"
    assert envelope.interaction_id == "int_1"
    assert envelope.captured_at == NOW
    assert envelope.loaded_datasets == ("bom", "inventory", "material")
    assert len(envelope.bkn_receipts) == 3
    assert envelope.snapshot.materials["M1"]["purchase_fixedleadtime"] == "14"
    assert envelope.snapshot.bom_by_product["P1"][0]["material_code"] == "M1"
    assert envelope.snapshot.inv_by_material["M1"][0]["available_base_qty"] == "100"


def test_assemble_exposes_forecast_rows_and_index_when_required():
    rows = _rows()
    rows["forecast"] = [
        {"id": "F1", "material_number": "P1", "qty": "1015", "enddate": "2026-01-31"}
    ]
    required = REQUIRED + ("forecast",)
    envelope = _assembler().assemble(
        _ctx(rows=rows, bkn_receipts=_receipts(required)), required
    )

    assert envelope.loaded_datasets == ("bom", "forecast", "inventory", "material")
    assert envelope.snapshot.forecast[0]["material_number"] == "P1"
    assert envelope.snapshot.forecast_by_id["F1"]["qty"] == "1015"


def test_assemble_reports_duplicate_forecast_ids_as_schema_mismatch():
    rows = _rows()
    rows["forecast"] = [{"id": "F1", "qty": "10"}, {"id": "F1", "qty": "20"}]
    required = REQUIRED + ("forecast",)

    with pytest.raises(SchemaMismatch) as err:
        _assembler().assemble(
            _ctx(rows=rows, bkn_receipts=_receipts(required)), required
        )
    assert err.value.code == "schema_mismatch"
    assert "F1" in str(err.value)


def test_assemble_default_source_is_openbkn_and_enforces_receipts():
    with pytest.raises(ReceiptRequired):
        _assembler().assemble(_ctx(bkn_receipts=()), REQUIRED)


def test_envelope_is_immutable():
    envelope = _assembler().assemble(_ctx(), REQUIRED)
    with pytest.raises(dataclasses.FrozenInstanceError):
        envelope.snapshot_id = "snap_forged"


def test_assemble_rejects_missing_context():
    with pytest.raises(ContextRequired) as err:
        _assembler().assemble(None, REQUIRED)
    assert err.value.code == "context_required"


def test_assemble_rejects_wrong_knowledge_network():
    with pytest.raises(ContextRequired) as err:
        _assembler().assemble(_ctx(knowledge_network_id="other_kn"), REQUIRED)
    assert "supply_ontology_hand" in str(err.value)


@pytest.mark.parametrize("field", ["conversation_id", "interaction_id"])
def test_assemble_rejects_blank_managed_ids(field):
    with pytest.raises(ContextRequired) as err:
        _assembler().assemble(_ctx(**{field: "  "}), REQUIRED)
    assert field in str(err.value)


def test_assemble_rejects_stale_context():
    stale_now = NOW + timedelta(seconds=DEFAULT_MAX_AGE_SECONDS + 1)
    with pytest.raises(ContextStale) as err:
        _assembler(now=stale_now).assemble(_ctx(), REQUIRED)
    assert err.value.code == "context_stale"


def test_assemble_max_age_is_configurable():
    later = NOW + timedelta(hours=2)
    envelope = _assembler(now=later, max_age_seconds=7200).assemble(_ctx(), REQUIRED)
    assert envelope.captured_at == NOW


def test_assemble_rejects_missing_required_dataset():
    rows = _rows()
    rows.pop("inventory")
    with pytest.raises(SnapshotIncomplete) as err:
        _assembler().assemble(_ctx(rows=rows), REQUIRED)
    assert err.value.code == "snapshot_incomplete"
    assert "inventory" in str(err.value)


def test_assemble_rejects_dataset_without_receipt():
    with pytest.raises(ReceiptRequired) as err:
        _assembler().assemble(_ctx(bkn_receipts=_receipts(("material", "bom"))), REQUIRED)
    assert err.value.code == "receipt_required"
    assert "inventory" in str(err.value)


def test_assemble_rejects_receipt_from_other_interaction():
    receipts = _receipts(("material", "bom")) + _receipts(("inventory",), interaction_id="int_2")
    with pytest.raises(ReceiptRequired) as err:
        _assembler().assemble(_ctx(bkn_receipts=receipts), REQUIRED)
    assert "inventory" in str(err.value)


def test_assemble_allows_empty_dataset_without_receipt():
    rows = _rows()
    rows["inventory"] = []
    envelope = _assembler().assemble(
        _ctx(rows=rows, bkn_receipts=_receipts(("material", "bom"))), REQUIRED
    )
    assert envelope.snapshot.inventory == []
    assert envelope.loaded_datasets == ("bom", "inventory", "material")


def test_assemble_rejects_unknown_source():
    with pytest.raises(SchemaMismatch) as err:
        _assembler().assemble(_ctx(), REQUIRED, source="csv")
    assert err.value.code == "schema_mismatch"


def test_assemble_requires_non_empty_required_datasets_argument():
    with pytest.raises(SnapshotIncomplete):
        _assembler().assemble(_ctx(), ())


# --- 组装：offline_test -------------------------------------------------


def test_offline_test_source_skips_receipt_and_interaction_checks():
    ctx = _ctx(conversation_id="", interaction_id="", bkn_receipts=())
    envelope = _assembler(now=NOW + timedelta(days=30)).assemble(
        ctx, REQUIRED, source=SOURCE_OFFLINE_TEST
    )
    assert envelope.source == SOURCE_OFFLINE_TEST
    assert envelope.bkn_receipts == ()
    assert envelope.snapshot.materials["M1"]["material_code"] == "M1"


def test_offline_test_still_requires_datasets():
    rows = _rows()
    rows.pop("bom")
    ctx = _ctx(rows=rows, bkn_receipts=())
    with pytest.raises(SnapshotIncomplete):
        _assembler().assemble(ctx, REQUIRED, source=SOURCE_OFFLINE_TEST)


# --- input_digest / snapshot_id ----------------------------------------


def test_input_digest_is_stable_for_equivalent_canonical_rows():
    rows_a = {"bom": [{"material_code": "M1", "standard_usage": "2"}]}
    rows_b = {"bom": [{"standard_usage": "2", "material_code": "M1"}]}
    digest = compute_input_digest(rows_a)
    assert len(digest) == 64
    assert digest == compute_input_digest(rows_b)


def test_input_digest_changes_when_rows_change():
    base = compute_input_digest(_rows())
    changed = _rows()
    changed["inventory"][0]["available_base_qty"] = "101"
    assert compute_input_digest(changed) != base


def test_input_digest_covers_only_loaded_datasets():
    rows = _rows()
    rows["forecast"] = [{"forecast_id": "F1", "qty": "10"}]
    envelope = _assembler().assemble(_ctx(rows=rows), REQUIRED)
    assert envelope.input_digest == compute_input_digest(_rows())


def test_snapshot_id_is_stable_and_derived_from_digest():
    first = _assembler().assemble(_ctx(), REQUIRED)
    second = _assembler().assemble(_ctx(), REQUIRED)
    assert first.snapshot_id == second.snapshot_id
    assert first.input_digest == second.input_digest
    assert first.snapshot_id.startswith("snap_")
    assert first.input_digest.startswith(first.snapshot_id.removeprefix("snap_"))


def test_snapshot_id_differs_for_different_input():
    first = _assembler().assemble(_ctx(), REQUIRED)
    changed = _rows()
    changed["inventory"][0]["available_base_qty"] = "999"
    second = _assembler().assemble(_ctx(rows=changed), REQUIRED)
    assert first.snapshot_id != second.snapshot_id


def test_assembler_does_not_mutate_resolved_context_rows():
    ctx = _ctx()
    envelope = _assembler().assemble(ctx, REQUIRED)
    envelope.snapshot.bom[0]["material_code"] = "TOUCHED"
    envelope.snapshot.inventory.append({"material_code": "EXTRA"})
    assert ctx.rows["bom"][0]["material_code"] == "M1"
    assert len(ctx.rows["inventory"]) == 1


# --- build_snapshot / load_csv_snapshot --------------------------------


def test_build_snapshot_supports_dataset_aliases():
    rows = {
        "material": [{"material_code": "M1"}],
        "bom": [{"bom_material_code": "P1", "material_code": "M1"}],
        "inventory": [{"material_code": "M1"}],
        "po": [{"material_number": "M1", "billno": "PO1"}],
        "pr": [{"material_number": "M1", "billno": "PR1"}],
        "mrp": [{"materialplanid_number": "M1", "billno": "MRP1"}],
    }
    snap = build_snapshot(rows)
    assert snap.po_by_material["M1"][0]["billno"] == "PO1"
    assert snap.pr_by_material["M1"][0]["billno"] == "PR1"
    assert snap.mrp_by_material["M1"][0]["billno"] == "MRP1"

    long_names = build_snapshot(
        {
            "purchase_order": rows["po"],
            "purchase_request": rows["pr"],
        }
    )
    assert long_names.po_by_material["M1"][0]["billno"] == "PO1"
    assert long_names.pr_by_material["M1"][0]["billno"] == "PR1"


def test_build_snapshot_ignores_unknown_datasets_and_empty_input():
    snap = build_snapshot({"sales_order": [{"billno": "SO1"}]})
    assert snap.bom == []
    assert snap.materials == {}
    assert snap.forecast == []
    assert snap.forecast_by_id == {}
    empty = build_snapshot()
    assert empty.inventory == []
    assert empty.forecast == []
    assert empty.forecast_by_id == {}


def test_build_snapshot_keeps_forecast_rows_and_indexes_by_id():
    rows = {
        "forecast": [
            {"id": "F1", "material_number": "P1", "qty": "10", "enddate": "2026-01-31"},
            {"forecast_id": "F2", "material_number": "P2", "qty": "20"},
        ]
    }
    snap = build_snapshot(rows)

    assert [row["material_number"] for row in snap.forecast] == ["P1", "P2"]
    assert set(snap.forecast_by_id) == {"F1", "F2"}
    assert snap.forecast_by_id["F1"]["qty"] == "10"
    assert snap.forecast_by_id["F1"]["enddate"] == "2026-01-31"
    assert snap.forecast_by_id["F2"]["material_number"] == "P2"


def test_build_snapshot_forecast_index_skips_blank_ids_but_keeps_rows():
    rows = {
        "forecast": [
            {"id": "  F1  ", "material_number": "P1"},
            {"id": "", "forecast_id": "", "material_number": "P2"},
            {"material_number": "P3"},
        ]
    }
    snap = build_snapshot(rows)

    assert len(snap.forecast) == 3
    assert set(snap.forecast_by_id) == {"F1"}
    assert snap.forecast_by_id["F1"]["material_number"] == "P1"


def test_build_snapshot_forecast_index_falls_back_when_id_is_whitespace():
    snap = build_snapshot(
        {"forecast": [{"id": "   ", "forecast_id": "F-fallback"}]}
    )
    assert set(snap.forecast_by_id) == {"F-fallback"}


def test_build_snapshot_rejects_duplicate_forecast_ids():
    with pytest.raises(ValueError) as err:
        build_snapshot(
            {"forecast": [{"id": "F1", "qty": "10"}, {"id": " F1 ", "qty": "20"}]}
        )
    assert "F1" in str(err.value)


def test_build_snapshot_rejects_duplicate_forecast_id_after_fallback():
    with pytest.raises(ValueError) as err:
        build_snapshot(
            {"forecast": [{"id": "F1"}, {"id": "   ", "forecast_id": "F1"}]}
        )
    assert "F1" in str(err.value)


def test_build_snapshot_forecast_does_not_disturb_other_indexes():
    rows = {
        "forecast": [{"id": "F1", "material_number": "P1"}],
        "material": [{"material_code": "M1"}],
        "bom": [{"bom_material_code": "P1", "material_code": "M1"}],
        "inventory": [{"material_code": "M1"}],
        "purchase_order": [{"material_number": "M1", "billno": "PO1"}],
        "purchase_request": [{"material_number": "M1", "billno": "PR1"}],
        "mrp": [{"materialplanid_number": "M1", "billno": "MRP1"}],
    }
    snap = build_snapshot(rows)

    assert set(snap.materials) == {"M1"}
    assert snap.bom_by_product["P1"][0]["material_code"] == "M1"
    assert snap.inv_by_material["M1"][0]["material_code"] == "M1"
    assert snap.po_by_material["M1"][0]["billno"] == "PO1"
    assert snap.pr_by_material["M1"][0]["billno"] == "PR1"
    assert snap.mrp_by_material["M1"][0]["billno"] == "MRP1"
    assert set(snap.forecast_by_id) == {"F1"}


def test_build_snapshot_does_not_mutate_input_forecast_rows():
    rows = {"forecast": [{"id": "F1", "material_number": "P1"}]}
    original = [dict(row) for row in rows["forecast"]]

    snap = build_snapshot(rows)
    snap.forecast[0]["material_number"] = "TOUCHED"
    snap.forecast.append({"id": "EXTRA"})

    assert rows["forecast"] == original
    assert set(snap.forecast_by_id) == {"F1"}
    assert snap.forecast_by_id["F1"]["material_number"] == "TOUCHED"


def test_build_snapshot_does_not_mutate_input_rows():
    rows = {"bom": [{"bom_material_code": "P1", "material_code": "M1"}]}
    original = [dict(r) for r in rows["bom"]]
    snap = build_snapshot(rows)
    snap.bom[0]["material_code"] = "TOUCHED"
    snap.bom.append({"material_code": "EXTRA"})
    assert rows["bom"] == original


def _write_min_csvs(target: Path) -> None:
    files = {
        "erp_material.csv": (
            ["material_code", "materialattr", "purchase_fixedleadtime"],
            [["TMP-1", "外购", "7"]],
        ),
        "erp_material_bom.csv": (
            ["bom_material_code", "bom_level", "material_code", "standard_usage"],
            [["TMP-P", "1", "TMP-1", "1"]],
        ),
        "erp_real_time_inventory.csv": (
            ["material_code", "warehouse", "available_base_qty"],
            [["TMP-1", "苏州半成品仓", "5"]],
        ),
        "erp_purchase_order.csv": (["material_number", "billno"], [["TMP-1", "PO-T"]]),
        "erp_purchase_request.csv": (["material_number", "billno"], [["TMP-1", "PR-T"]]),
        "erp_mrp_plan_order.csv": (["materialplanid_number", "billno"], [["TMP-1", "MRP-T"]]),
        "erp_mds_forecast.csv": (
            ["id", "material_number", "enddate", "qty"],
            [["FC-TMP", "TMP-P", "2026-08-31", "1"]],
        ),
    }
    for name, (header, body) in files.items():
        with (target / name).open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(header)
            writer.writerows(body)


def test_load_csv_snapshot_data_dir_does_not_pollute_default(tmp_path):
    default_data = snapshot_module.DATA
    _write_min_csvs(tmp_path)

    local = load_csv_snapshot(tmp_path)
    assert set(local.materials) == {"TMP-1"}

    assert snapshot_module.DATA == default_data
    again = load_csv_snapshot()
    assert "TMP-1" not in again.materials
    assert len(again.materials) > 100
