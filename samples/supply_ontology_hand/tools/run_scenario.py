#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scenario.runner import FulfillmentCommitmentRunner


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the offline fulfillment commitment story")
    parser.add_argument("--scenario", choices=["fulfillment-commitment"], required=True)
    parser.add_argument("--product", required=True)
    parser.add_argument("--forecast-id", required=True)
    parser.add_argument("--demand-end", required=True)
    parser.add_argument("--demand-qty", type=float, required=True)
    parser.add_argument("--substitute-enabled", action="store_true")
    parser.add_argument("--report-grain", choices=["summary", "full_tree"], default="summary")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    report = FulfillmentCommitmentRunner(Path(__file__).resolve().parents[1] / "data").run(product=args.product, forecast_id=args.forecast_id, demand_end=args.demand_end, demand_qty=args.demand_qty, substitute_enabled=args.substitute_enabled, report_grain=args.report_grain)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"wrote report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
