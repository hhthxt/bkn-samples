from __future__ import annotations

from collections import defaultdict

from .errors import CannotCompute
from .inventory import available_qty, in_transit_qty
from .kitting import kitting_net_demand
from .warehouse import resolve_warehouse_scope


def shared_contention(
    snap,
    demands: list[dict],
    *,
    warehouse_scope: str | list[str] | None = "production_available",
    substitute_enabled: bool | None = False,
) -> dict:
    """Deduct shared available+in-transit in demand list order."""
    if not demands or len(demands) < 2:
        raise CannotCompute("共用料争用至少需要 2 条需求")
    if substitute_enabled is None:
        raise CannotCompute("未确认是否启用替代料，不能算争用")

    normalized = []
    for item in demands:
        product = (item.get("product") or item.get("product_code") or "").strip()
        qty = item.get("qty", item.get("demand_qty"))
        if not product:
            raise CannotCompute("需求缺少产品编码")
        if qty is None:
            raise CannotCompute(f"{product} 缺少数量，不能算争用（数量未定请改用产品 BOM 共用清单）")
        normalized.append({"product_code": product, "qty": float(qty)})

    warehouses = resolve_warehouse_scope(warehouse_scope)
    per_demand = []
    pool: dict[str, float] = defaultdict(float)
    seen_materials: dict[str, int] = defaultdict(int)
    for dem in normalized:
        kit = kitting_net_demand(
            snap,
            dem["product_code"],
            dem["qty"],
            warehouse_scope=warehouse_scope,
            substitute_enabled=substitute_enabled,
        )
        per_demand.append(kit)
        for line in kit["lines"]:
            code = line["material_code"]
            seen_materials[code] += 1
            if code not in pool:
                pool[code] = available_qty(snap, code, warehouse_scope) + in_transit_qty(
                    snap, code
                )

    remaining = dict(pool)
    allocations = []
    for kit in per_demand:
        rows = []
        ok = True
        for line in kit["lines"]:
            code = line["material_code"]
            need = float(line["gross_requirement"])
            have = remaining.get(code, 0.0)
            take = min(have, need)
            remaining[code] = have - take
            short = max(0.0, need - take)
            if short > 0:
                ok = False
            rows.append(
                {
                    "material_code": code,
                    "gross_requirement": need,
                    "allocated": take,
                    "shortage": short,
                    "shared": seen_materials[code] > 1,
                }
            )
        allocations.append(
            {
                "product_code": kit["product_code"],
                "demand_qty": kit["demand_qty"],
                "satisfied": ok,
                "lines": rows,
            }
        )
    return {
        "demands": normalized,
        "allocations": allocations,
        "remaining": remaining,
        "warehouse_scope": warehouse_scope if not isinstance(warehouse_scope, list) else "custom",
        "warehouse_filter": warehouses,
        "substitute_enabled": bool(substitute_enabled),
        "deduction_order": [d["product_code"] for d in normalized],
    }
