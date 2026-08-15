#!/usr/bin/env python3
"""Offline CLI for supply_ontology_hand function library (CSV gold)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from fn import (  # noqa: E402
    CannotCompute,
    backward_plan,
    bom_list,
    bom_shared_list,
    kitting_net_demand,
    layered_inventory,
    leadtime_days,
    load_csv_snapshot,
    max_build_without_po,
    shared_contention,
    substitute_status,
    supply_status,
    theoretical_build,
    total_sellable,
)


def _bool_arg(val: str | None):
    if val is None:
        return None
    text = str(val).strip().lower()
    if text in ("1", "true", "yes", "y", "是"):
        return True
    if text in ("0", "false", "no", "n", "否"):
        return False
    raise argparse.ArgumentTypeError("substitute 必须是 yes/no")


def _dump(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="supply_ontology_hand 函数 CLI（CSV 快照）")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("bom-list")
    p.add_argument("--product", required=True)
    p.add_argument("--depth", type=int, default=1)
    p.add_argument("--full", action="store_true")
    p.add_argument("--include-substitute", action="store_true")

    p = sub.add_parser("bom-shared")
    p.add_argument("--products", required=True, help="逗号分隔，至少 2 个")
    p.add_argument("--include-substitute", action="store_true")

    p = sub.add_parser("layered")
    p.add_argument("--product", required=True)
    p.add_argument("--depth", type=int, default=1)
    p.add_argument("--warehouse-scope", default="production_available")

    p = sub.add_parser("substitute")
    p.add_argument("--product", required=True)

    p = sub.add_parser("theoretical")
    p.add_argument("--product", required=True)
    p.add_argument("--substitute", required=True)
    p.add_argument("--warehouse-scope", default="production_available")

    p = sub.add_parser("sellable")
    p.add_argument("--product", required=True)
    p.add_argument("--substitute", required=True)

    p = sub.add_parser("max-build")
    p.add_argument("--product", required=True)
    p.add_argument("--substitute", required=True)

    p = sub.add_parser("kitting")
    p.add_argument("--product", required=True)
    p.add_argument("--qty", type=float, required=True)
    p.add_argument("--substitute", required=True)
    p.add_argument("--warehouse-scope", default="production_available")

    p = sub.add_parser("contention")
    p.add_argument("--demands", required=True, help="382-000005:50,P61-000351:60")
    p.add_argument("--substitute", required=True)

    p = sub.add_parser("leadtime")
    p.add_argument("--material", required=True)

    p = sub.add_parser("supply-status")
    p.add_argument("--material", required=True)
    p.add_argument("--due-date")
    p.add_argument("--gross", type=float, default=0)

    p = sub.add_parser("backward-plan")
    p.add_argument("--product", required=True)
    p.add_argument("--forecast-id", required=True)
    p.add_argument("--demand-end", required=True)
    p.add_argument("--qty", type=float, required=True)
    p.add_argument("--substitute", required=True)
    p.add_argument("--warehouse-scope", default="production_available")
    p.add_argument("--report-grain", default="summary")

    args = parser.parse_args(argv)
    snap = load_csv_snapshot()
    try:
        if args.cmd == "bom-list":
            depth = None if args.full else args.depth
            _dump(bom_list(snap, args.product, depth=depth, include_substitute=args.include_substitute))
        elif args.cmd == "bom-shared":
            products = [x.strip() for x in args.products.split(",") if x.strip()]
            _dump(bom_shared_list(snap, products, include_substitute=args.include_substitute))
        elif args.cmd == "layered":
            _dump(layered_inventory(snap, args.product, depth=args.depth, warehouse_scope=args.warehouse_scope))
        elif args.cmd == "substitute":
            _dump(substitute_status(snap, args.product))
        elif args.cmd == "theoretical":
            _dump(theoretical_build(snap, args.product, warehouse_scope=args.warehouse_scope, substitute_enabled=_bool_arg(args.substitute)))
        elif args.cmd == "sellable":
            _dump(total_sellable(snap, args.product, substitute_enabled=_bool_arg(args.substitute)))
        elif args.cmd == "max-build":
            _dump(max_build_without_po(snap, args.product, substitute_enabled=_bool_arg(args.substitute)))
        elif args.cmd == "kitting":
            _dump(kitting_net_demand(snap, args.product, args.qty, warehouse_scope=args.warehouse_scope, substitute_enabled=_bool_arg(args.substitute)))
        elif args.cmd == "contention":
            demands = []
            for part in args.demands.split(","):
                code, qty = part.split(":", 1)
                demands.append({"product": code.strip(), "qty": float(qty)})
            _dump(shared_contention(snap, demands, substitute_enabled=_bool_arg(args.substitute)))
        elif args.cmd == "leadtime":
            _dump({"material_code": args.material, "leadtime_days": leadtime_days(snap, args.material)})
        elif args.cmd == "supply-status":
            _dump(supply_status(snap, args.material, due_date=args.due_date, gross_requirement=args.gross))
        elif args.cmd == "backward-plan":
            _dump(
                backward_plan(
                    snap,
                    args.product,
                    forecast_id=args.forecast_id,
                    demand_end=args.demand_end,
                    demand_qty=args.qty,
                    warehouse_scope=args.warehouse_scope,
                    substitute_enabled=_bool_arg(args.substitute),
                    report_grain=args.report_grain,
                )
            )
    except CannotCompute as exc:
        print(json.dumps({"error": "cannot_compute", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
