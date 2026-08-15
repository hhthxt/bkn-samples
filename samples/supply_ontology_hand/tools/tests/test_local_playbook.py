from datetime import datetime, timezone
from pathlib import Path

import pytest

from actions.approval import ApprovalAuthority, ApprovalReplay, ApprovalRequired
from actions.monitor_task import close_monitor_task, create_monitor_task
from actions.monitor_runner import MonitorRunner
from actions.pr_decision import create_pr_decision
from actions.store import LocalActionStore
from metrics import LocalMetricCalculator
from scenario.runner import FulfillmentCommitmentRunner


PACK = Path(__file__).parents[2]
NOW = datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc)
SECRET = "local-sample-secret"


def test_local_metrics_match_business_baseline():
    metrics = LocalMetricCalculator.from_csv(PACK / "data")
    assert metrics.calculate("product_count")["value"] == 30
    assert metrics.calculate("material_count")["value"] == 3497
    assert metrics.calculate("supplier_count")["value"] == 230
    assert metrics.calculate("sales_order_count")["value"] == 800
    assert metrics.calculate("warehouse_count")["value"] == 29
    assert metrics.calculate("available_inventory_qty", product_code="382-000005", warehouse_scope="finished_goods")["value"] == 534
    assert metrics.calculate("forecast_demand_qty")["value"] == 46840
    assert metrics.calculate("open_forecast_count")["value"] == 87


def test_story_runner_connects_s1_s2_and_s3():
    report = FulfillmentCommitmentRunner(PACK / "data").run(
        product="U00-000080",
        forecast_id="0000023181",
        demand_end="2026-05-31",
        demand_qty=3000,
        substitute_enabled=False,
        demands=[
            {"product_code": "U00-000080", "qty": 3000},
            {"product_code": "382-000005", "qty": 10},
        ],
    )
    assert [step["id"] for step in report["steps"]] == ["s1", "s2", "s3"]
    assert report["steps"][0]["result"]["max_delay_days"] == 166
    assert report["steps"][1]["result"]["total_sellable_qty"] == 20
    assert report["snapshot_meta"]["source"] == "offline_test"


def test_actions_require_approval_and_preserve_audit_evidence():
    authority = ApprovalAuthority(SECRET)
    store = LocalActionStore()
    decision = {
        "action_type": "create_pr_decision",
        "interaction_id": "int-1",
        "idempotency_key": "idem-1",
        "decision_batch_id": "batch-1",
        "forecast_id": "fcst-1",
        "product_code": "P-1",
        "material_code": "M-1",
        "recommended_qty": 4,
        "snapshot_id": "snap-1",
    }
    with pytest.raises(ApprovalRequired):
        create_pr_decision(decision, None, store=store, secret=SECRET, now=NOW)
    token = authority.issue(decision, action_type=decision["action_type"], interaction_id="int-1", approver="planner", idempotency_key="idem-1", now=NOW)
    created = create_pr_decision(decision, token, store=store, secret=SECRET, now=NOW)
    assert created["dry_run"] is True
    with pytest.raises(ApprovalReplay):
        create_pr_decision(decision, token, store=store, secret=SECRET, now=NOW)

    task = {
        "action_type": "create_monitor_task",
        "interaction_id": "int-2",
        "idempotency_key": "idem-task",
        "task_id": "task-1",
        "product_code": "P-1",
        "forecast_id": "fcst-1",
        "forecast_qty": 10,
        "snapshot_id": "snap-2",
        "s1_result": {"can_deliver_on_time": False, "max_delay_days": 3, "nodes": []},
    }
    task_token = authority.issue(task, action_type=task["action_type"], interaction_id="int-2", approver="planner", idempotency_key="idem-task", now=NOW)
    create_monitor_task(task, task_token, store=store, secret=SECRET, now=NOW)
    close = {"action_type": "close_monitor_task", "interaction_id": "int-2", "idempotency_key": "idem-close", "task_id": "task-1", "reason": "closed"}
    close_token = authority.issue(close, action_type=close["action_type"], interaction_id="int-2", approver="planner", idempotency_key="idem-close", now=NOW)
    result = close_monitor_task(close, close_token, store=store, secret=SECRET, now=NOW)
    assert result["task_status"] == "closed"
    assert "task-1" in store.items


def test_monitor_runner_refreshes_open_tasks_without_deleting_evidence():
    store = LocalActionStore()
    store.tasks["task-1"] = {"task_id": "task-1", "task_status": "watching", "snapshot_id": "old"}
    store.items["task-1"] = [{"item_id": "item-1"}]
    result = MonitorRunner(store).run_once({"task-1": {"can_deliver_on_time": False, "max_delay_days": 5, "snapshot_id": "new", "nodes": []}}, now=NOW)
    assert result["updated"] == 1
    assert store.tasks["task-1"]["task_status"] == "risk"
    assert store.tasks["task-1"]["snapshot_id"] == "new"
