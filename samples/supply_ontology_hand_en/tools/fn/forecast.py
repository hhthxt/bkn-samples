"""Count open (not closed) forecast documents from inline rows."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

CLOSED_STATUS = "Closed"


def open_forecast_count(
    forecast_rows: Iterable[Mapping[str, Any]] | None,
    *,
    product_code: str | None = None,
) -> dict[str, Any]:
    rows = [dict(row) for row in (forecast_rows or [])]
    product = (product_code or "").strip() or None
    open_ids: list[str] = []
    excluded_closed = 0
    for row in rows:
        code = str(row.get("material_number") or "").strip()
        if product and code != product:
            continue
        if str(row.get("closestatus_title") or "").strip() in ("已关闭", CLOSED_STATUS):
            excluded_closed += 1
            continue
        open_ids.append(str(row.get("id") or row.get("forecast_id") or "").strip())
    return {
        "open_count": len(open_ids),
        "excluded_closed_count": excluded_closed,
        "input_row_count": len(rows),
        "product_code": product,
        "exclusion": {
            "field": "closestatus_title",
            "operation": "!=",
            "value": CLOSED_STATUS,
        },
        "open_forecast_ids": open_ids,
    }
