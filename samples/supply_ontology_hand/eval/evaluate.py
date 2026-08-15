from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from metrics import LocalMetricCalculator
from scenario.runner import FulfillmentCommitmentRunner

SUPPORTED = {"metric", "function", "scenario"}


def load_cases(directory: str | Path) -> dict[str, list[dict[str, Any]]]:
    result = {}
    for name in ("metrics", "functions", "scenarios"):
        with (Path(directory) / f"{name}.yaml").open(encoding="utf-8") as stream:
            rows = yaml.safe_load(stream) or []
        for row in rows:
            if row.get("kind") not in SUPPORTED:
                raise ValueError(f"unsupported case kind: {row.get('kind')}")
        result[name] = rows
    return result


def evaluate_local_sample(data_dir: str | Path, cases_dir: str | Path) -> dict[str, Any]:
    cases = load_cases(cases_dir)
    calc = LocalMetricCalculator.from_csv(data_dir)
    metric_results = [_check(case["id"], calc.calculate(case["metric_id"], **(case.get("filters") or {}))["value"], case["expected"]) for case in cases["metrics"]]
    runner = FulfillmentCommitmentRunner(data_dir)
    function_results, scenario_results = [], []
    for group, target in (("functions", function_results), ("scenarios", scenario_results)):
        for case in cases[group]:
            args = {key: case[key] for key in ("product", "forecast_id", "demand_end", "demand_qty", "substitute_enabled", "report_grain") if key in case}
            report = runner.run(**args)
            target.extend(_check(f"{case['id']}.{index}", _path(report, assertion["path"]), assertion["expected"]) for index, assertion in enumerate(case.get("assertions") or []))
    def accuracy(rows): return sum(1 for row in rows if row["passed"]) / len(rows) if rows else 1.0
    governance = all(proposal.get("status") == "proposed" for case in cases["scenarios"] for proposal in runner.run(**{key: case[key] for key in ("product", "forecast_id", "demand_end", "demand_qty", "substitute_enabled") if key in case}).get("action_proposals", []))
    result = {"metric_accuracy": accuracy(metric_results), "function_accuracy": accuracy(function_results), "scenario_accuracy": accuracy(scenario_results), "governance_boundary_accuracy": 1.0 if governance else 0.0, "total_cases": len(metric_results) + len(function_results) + len(scenario_results)}
    result["passed"] = all((result["metric_accuracy"] >= .95, result["function_accuracy"] >= .95, result["scenario_accuracy"] >= .95, governance))
    result["details"] = {"metrics": metric_results, "functions": function_results, "scenarios": scenario_results}
    return result


def _path(value: Any, path: str) -> Any:
    for part in path.split("."):
        value = value[int(part)] if part.isdigit() else value[part]
    return value


def _check(case_id: str, actual: Any, expected: Any) -> dict[str, Any]:
    passed = abs(float(actual) - float(expected)) <= max(1e-6, abs(float(expected)) * .001) if isinstance(actual, (int, float)) and isinstance(expected, (int, float)) else actual == expected
    return {"id": case_id, "actual": actual, "expected": expected, "passed": passed}
