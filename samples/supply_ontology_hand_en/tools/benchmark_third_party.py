"""Third-party behavioral benchmark.

This runner intentionally extracts only case ids and user questions from the
QA YAML. It never accesses reference fields. Numerical correctness is covered
by the independent local evaluator; this file measures whether a customer or
ecosystem Agent can move through the public conversation contract safely.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from actions.approval import ApprovalAuthority
from actions.store import LocalActionStore
from dialogue.playbook import ConversationPlaybook


def _question_cases(path: Path) -> list[dict[str, str]]:
    # Importing YAML is deliberately avoided: reference values live beside
    # questions in the same YAML document. This line parser only accepts the
    # public id/question pair and skips all other fields.
    cases: list[dict[str, str]] = []
    pending_id: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if "question:" in line and "id:" in line and line.startswith("-"):
            match = re.search(r"id:\s*([^,}]+).*question:\s*([^,}]+)", line)
            if match:
                cases.append({"id": match.group(1).strip().strip("'\""), "question": match.group(2).strip().strip("'\"")})
                pending_id = None
                continue
        if line.startswith("- id:"):
            pending_id = line.split(":", 1)[1].strip().strip("'\"")
        elif line.startswith("id:"):
            pending_id = line.split(":", 1)[1].strip().strip("'\"")
        elif "question:" in line and pending_id:
            question = line.split("question:", 1)[1].strip().strip("'\"")
            cases.append({"id": pending_id, "question": question})
            pending_id = None
    return cases


def _assert_case(case_id: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": case_id, "passed": passed, "detail": detail}


def run_playbook(data_dir: Path) -> list[dict[str, Any]]:
    now = datetime(2026, 8, 15, tzinfo=timezone.utc)
    store = LocalActionStore()
    playbook = ConversationPlaybook(data_dir, store=store, now=now)
    results: list[dict[str, Any]] = []

    first = playbook.start()
    results.append(_assert_case("PB-01", first["state"] == "collecting_context" and bool(first["missing_fields"]), "不完整输入被转成澄清字段"))

    context = {
        "type": "provide_context",
        "product": "U00-000080",
        "forecast_id": "0000023181",
        "demand_end": "2026-05-31",
        "demand_qty": 3000,
        "substitute_enabled": False,
    }
    s1 = playbook.handle(context)
    results.append(_assert_case("PB-02", s1["state"] == "awaiting_s1_review" and bool(s1["visible_steps"]) and bool(s1["snapshot_meta"]), "补齐上下文后先返回 S1 证据"))

    s2 = playbook.handle({"type": "continue", "step": "s2"})
    results.append(_assert_case("PB-03", s2["state"] == "awaiting_s3_or_action" and {x["id"] for x in s2["visible_steps"]} == {"s1", "s2"}, "S2 必须在 S1 审阅后继续"))

    proposed = playbook.handle({"type": "propose_action", "action": "create_monitor_task"})
    results.append(_assert_case("PB-04", proposed["state"] == "awaiting_human_confirmation", "Action 先提议，未直接写入"))

    try:
        playbook.handle({"type": "confirm_action", "action": "create_monitor_task"})
    except Exception as exc:  # noqa: BLE001 - the contract is the assertion
        blocked = "approval" in str(exc).lower() or "token" in str(exc).lower()
    else:
        blocked = False
    results.append(_assert_case("PB-05", blocked, "缺少人工批准凭证时拒绝执行"))

    proposal = playbook.pending_actions["create_monitor_task"]
    token = ApprovalAuthority("local-dialogue-secret").issue(
        proposal,
        action_type="create_monitor_task",
        interaction_id=proposal["interaction_id"],
        approver="customer-planner",
        idempotency_key=proposal["idempotency_key"],
        now=now,
    )
    done = playbook.handle({"type": "confirm_action", "action": "create_monitor_task", "approval_token": token})
    results.append(_assert_case("PB-06", done["state"] == "action_completed" and bool(done["result"].get("task_id")) and done["result"].get("dry_run") is True, "批准后返回可追踪 dry-run 回执"))
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--qa-file", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    cases = _question_cases(Path(args.qa_file))
    playbook = run_playbook(Path(args.data_dir))
    result = {
        "benchmark": "third_party_behavioral_blind",
        "reference_answers_read": False,
        "question_cases_loaded": len(cases),
        "playbook_cases": playbook,
        "playbook_accuracy": sum(x["passed"] for x in playbook) / len(playbook),
        "passed": all(x["passed"] for x in playbook),
    }
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "playbook_cases"}, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
