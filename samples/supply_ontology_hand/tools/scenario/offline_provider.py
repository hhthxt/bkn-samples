from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from context.contract import ResolvedContext, SnapshotIncomplete

FILES = {
    "bom": "erp_material_bom.csv",
    "inventory": "erp_real_time_inventory.csv",
    "material": "erp_material.csv",
    "purchase_order": "erp_purchase_order.csv",
    "purchase_request": "erp_purchase_request.csv",
    "mrp": "erp_mrp_plan_order.csv",
    "forecast": "erp_mds_forecast.csv",
}
DATASETS = frozenset((*FILES, "product"))


def _read(base: Path, name: str) -> list[dict[str, str]]:
    with (base / FILES[name]).open(newline="", encoding="utf-8") as stream:
        return [dict(row) for row in csv.DictReader(stream)]


def _v(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return ""


class OfflineSnapshotProvider:
    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)

    def capture(self, *, datasets: Iterable[str], product: str | None = None, forecast_id: str | None = None) -> ResolvedContext:
        wanted = {str(name).strip() for name in datasets if str(name).strip()}
        if not wanted:
            raise SnapshotIncomplete("at least one dataset is required")
        unknown = wanted - DATASETS
        if unknown:
            raise SnapshotIncomplete(f"unknown dataset: {', '.join(sorted(unknown))}")
        raw = {name: _read(self.data_dir, name) for name in sorted(wanted) if name in FILES}
        bom = raw.get("bom", [])
        if product:
            bom = [row for row in bom if _v(row, "bom_material_code", "parent_material_code") == product or _v(row, "material_code") == product]
        codes = {_v(row, "material_code", "material_number") for row in bom}
        if product:
            codes.add(product)
        rows: dict[str, tuple[dict[str, str], ...]] = {}
        for name, source in raw.items():
            selected = source
            if name == "bom":
                selected = bom
            elif name == "forecast":
                selected = [row for row in source if (not forecast_id or _v(row, "id", "forecast_id") == forecast_id) and (not product or _v(row, "material_number", "product_code") == product)]
            elif product and name in {"material", "inventory", "purchase_order", "purchase_request", "mrp"}:
                keys = {"material": ("material_code", "material_number"), "inventory": ("material_code", "material_number"), "purchase_order": ("material_number", "material_code"), "purchase_request": ("material_number", "material_code"), "mrp": ("materialplanid_number", "material_code", "material_number")} [name]
                selected = [row for row in source if _v(row, *keys) in codes]
            rows[name] = tuple(dict(row) for row in selected)
        token = hashlib.sha256(f"{product}|{forecast_id}|{sorted(wanted)}".encode()).hexdigest()[:16]
        return ResolvedContext(knowledge_network_id="supply_ontology_hand", conversation_id=f"offline-{token}", interaction_id=f"offline-{token}", captured_at=datetime.now(timezone.utc), rows=rows, bkn_receipts=())
