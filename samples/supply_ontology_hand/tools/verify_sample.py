#!/usr/bin/env python3
"""Read-only release verifier for the public experience pack."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from eval.evaluate import evaluate_local_sample


def verify(pack: str | Path, *, run_tests: bool = True) -> dict[str, Any]:
    root = Path(pack)
    required = [
        root / "README.md",
        root / "docs/playbook/fulfillment-commitment-playbook.md",
        root / "docs/playbook/agent-conversation.md",
        root / "docs/quickstart/offline.md",
        root / "docs/quickstart/online-openbkn.md",
        root / "docs/catalog/metrics.md",
        root / "docs/catalog/functions.md",
        root / "docs/catalog/actions.md",
        root / "docs/power-layer/capability-registry.yaml",
        root / "tools/run_scenario.py",
        root / "tools/actions",
        root / "eval/cases/metrics.yaml",
    ]
    documentation_passed = all(path.exists() for path in required)
    test_process = None
    if run_tests:
        test_process = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "--disable-warnings"], cwd=root / "tools", capture_output=True, text=True, check=False)
    evaluation = evaluate_local_sample(root / "data", root / "eval/cases")
    tests_passed = None if test_process is None else test_process.returncode == 0
    passed = documentation_passed and evaluation["passed"] and (tests_passed is None or tests_passed)
    return {"passed": passed, "documentation_passed": documentation_passed, "tests_passed": tests_passed, "test_output": "" if test_process is None else test_process.stdout[-1000:], "evaluation": evaluation}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    report = verify(root)
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    raise SystemExit(0 if report["passed"] else 1)
