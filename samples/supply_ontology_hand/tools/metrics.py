"""Deterministic local implementations of the sample's P0 metrics."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable

from fn.warehouse import resolve_warehouse_scope

METRIC_FILES = {
    "product_count": "hd_product_view.csv",
    "material_count": "erp_material.csv",
    "supplier_count": "erp_supplier.csv",
    "sales_order_count": "sales_order.csv",
    "warehouse_count": "erp_real_time_inventory.csv",
    "available_inventory_qty": "erp_real_time_inventory.csv",
    "forecast_demand_qty": "erp_mds_forecast.csv",
    "open_forecast_count": "erp_mds_forecast.csv",
}


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return [dict(row) for row in csv.DictReader(stream)]


def _v(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return ""


def _where(rows: Iterable[dict[str, str]], key: str, value: Any) -> list[dict[str, str]]:
    return list(rows) if value is None else [row for row in rows if _v(row, key) == str(value).strip()]


def _num(value: Any) -> float:
    return float(value or 0)


def _whole(value: float) -> int | float:
    return int(value) if float(value).is_integer() else value


class LocalMetricCalculator:
    def __init__(self, datasets: dict[str, list[dict[str, str]]]):
        self.datasets = datasets

    @classmethod
    def from_csv(cls, data_dir: str | Path) -> "LocalMetricCalculator":
        base = Path(data_dir)
        names = {
            "product": "hd_product_view.csv",
            "material": "erp_material.csv",
            "supplier": "erp_supplier.csv",
            "sales_order": "sales_order.csv",
            "inventory": "erp_real_time_inventory.csv",
            "forecast": "erp_mds_forecast.csv",
        }
        return cls({name: _read(base / filename) for name, filename in names.items()})

    def calculate(self, metric_id: str, **filters: Any) -> dict[str, Any]:
        if metric_id not in METRIC_FILES:
            raise ValueError(f"unknown metric: {metric_id}")
        filters = {key: value for key, value in filters.items() if value is not None}
        if metric_id == "product_count":
            rows = self.datasets["product"]
            value = len({_v(row, "material_code", "material_number") for row in rows})
            evidence = rows
        elif metric_id == "material_count":
            evidence = _where(self.datasets["material"], "materialattr", filters.get("materialattr"))
            value = len({_v(row, "material_code") for row in evidence})
        elif metric_id == "supplier_count":
            evidence = _where(self.datasets["supplier"], "purchaserid_name", filters.get("purchaser"))
            value = len({_v(row, "supplier_code") for row in evidence})
        elif metric_id == "sales_order_count":
            evidence = _where(self.datasets["sales_order"], "product_code", filters.get("product_code"))
            value = len({_v(row, "sales_order_id") for row in evidence})
        elif metric_id == "warehouse_count":
            evidence = self.datasets["inventory"]
            value = len({_v(row, "warehouse") for row in evidence if _v(row, "warehouse")})
        elif metric_id == "available_inventory_qty":
            evidence = _where(self.datasets["inventory"], "material_code", filters.get("product_code"))
            allowed = set(resolve_warehouse_scope(filters.get("warehouse_scope", "production_available")))
            if allowed:
                evidence = [row for row in evidence if _v(row, "warehouse") in allowed]
            value = sum(_num(row.get("available_inventory_qty")) for row in evidence)
        elif metric_id == "forecast_demand_qty":
            evidence = self._forecast(filters)
            value = sum(_num(row.get("qty")) for row in evidence)
        else:
            evidence = self._forecast(filters)
            value = len({_v(row, "id", "forecast_id") for row in evidence})
        return {"metric_id": metric_id, "value": _whole(value), "filters": filters, "evidence": {"row_count": len(evidence), "source": "offline_test_csv", "source_file": METRIC_FILES[metric_id]}}

    def _forecast(self, filters: dict[str, Any]) -> list[dict[str, str]]:
        status = filters.get("status", "open")
        if status == "open":
            rows = [row for row in self.datasets["forecast"] if _v(row, "closestatus_title") not in ("已关闭", "Closed")]
        elif status == "closed":
            rows = [row for row in self.datasets["forecast"] if _v(row, "closestatus_title") in ("已关闭", "Closed")]
        else:
            raise ValueError(f"unknown forecast status: {status}")
        return _where(rows, "material_number", filters.get("product_code"))

    def calculate_all(self) -> dict[str, dict[str, Any]]:
        return {metric_id: self.calculate(metric_id) for metric_id in METRIC_FILES}
