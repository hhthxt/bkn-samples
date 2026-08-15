"""Shared offline resolved_context builder for service tests."""

from __future__ import annotations

import csv
from datetime import datetime, timezone

from fn.snapshot import DATA, load_csv_snapshot


def forecast_rows_from_csv() -> list[dict]:
    with (DATA / "erp_mds_forecast.csv").open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def csv_resolved_context(**overrides) -> dict:
    snap = load_csv_snapshot()
    payload = {
        "knowledge_network_id": "supply_ontology_hand",
        "conversation_id": "conv-test",
        "interaction_id": "int-test",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "bkn_receipts": [],
        "rows": {
            "bom": snap.bom,
            "inventory": snap.inventory,
            "purchase_order": snap.po,
            "purchase_request": snap.pr,
            "mrp": snap.mrp,
            "material": list(snap.materials.values()),
            "forecast": forecast_rows_from_csv(),
        },
    }
    payload.update(overrides)
    return payload
