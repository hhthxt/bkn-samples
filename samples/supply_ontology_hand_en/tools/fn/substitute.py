from __future__ import annotations

from .bom import is_substitute_row, product_bom_rows
from .errors import CannotCompute
from .inventory import available_qty
from .snapshot import Snapshot, _i


def substitute_status(
    snap: Snapshot,
    product: str,
    *,
    warehouse_scope: str | list[str] | None = "production_available",
    substitute_enabled: bool | None = None,
) -> dict:
    product = (product or "").strip()
    if not product:
        raise CannotCompute("缺少产品或物料编码")
    rows = product_bom_rows(snap, product)
    if not rows:
        raise CannotCompute(f"无 BOM：{product}")
    groups: dict[str, list[dict]] = {}
    for row in rows:
        if not is_substitute_row(row):
            continue
        gid = str(row.get("alt_group_no") or "").strip()
        groups.setdefault(gid, []).append(row)
    members = []
    for gid, items in sorted(groups.items(), key=lambda kv: kv[0]):
        members.append(
            {
                "alt_group_no": gid,
                "members": [
                    {
                        "material_code": (r.get("material_code") or "").strip(),
                        "material_name": (r.get("material_name") or "").strip(),
                        "alt_priority": _i(r.get("alt_priority"), 0),
                        "parent_material_code": (r.get("parent_material_code") or "").strip(),
                        "available_qty": available_qty(
                            snap,
                            (r.get("material_code") or "").strip(),
                            warehouse_scope,
                        ),
                    }
                    for r in items
                ],
            }
        )
    enabled = "unknown" if substitute_enabled is None else bool(substitute_enabled)
    return {
        "product_code": product,
        "has_alt_groups": bool(groups),
        "group_count": len(groups),
        "groups": members,
        "substitute_enabled": enabled,
        "warehouse_scope": warehouse_scope if not isinstance(warehouse_scope, list) else "custom",
    }
