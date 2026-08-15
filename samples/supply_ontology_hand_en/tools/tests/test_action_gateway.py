from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from actions.approval import ApprovalAuthority
from actions.store import LocalActionStore
from action_gateway import create_app


SECRET = "gateway-test-secret"
NOW = datetime(2026, 8, 15, tzinfo=timezone.utc)


def _proposal(action: str = "create_monitor_task") -> dict:
    return {
        "action_type": action,
        "interaction_id": "int-gateway-1",
        "snapshot_id": "snap-gateway-1",
        "forecast_id": "fc-1",
        "product_code": "P-1",
        "idempotency_key": "idem-gateway-1",
        "task_id": "task-fc-1",
        "forecast_qty": 10,
        "demand_end": "2026-08-31",
        "s1_result": {"status": "risk"},
    }


def _token(proposal: dict) -> str:
    return ApprovalAuthority(SECRET).issue(
        proposal,
        action_type=proposal["action_type"],
        interaction_id=proposal["interaction_id"],
        approver="planner",
        idempotency_key=proposal["idempotency_key"],
        now=NOW,
    )


def test_gateway_health_and_ready_are_safe_contracts():
    client = TestClient(create_app(store=LocalActionStore(), secret=SECRET, now=NOW))
    assert client.get("/health").json() == {"status": "ok"}
    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["actions"] == ["close_monitor_task", "create_monitor_task", "create_pr_decision"]


def test_gateway_rejects_missing_approval_before_action():
    client = TestClient(create_app(store=LocalActionStore(), secret=SECRET, now=NOW))
    proposal = _proposal()
    response = client.post("/actions/create_monitor_task", json={"proposal": proposal})
    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "approval_required"


def test_gateway_creates_only_dry_run_receipt_after_approval():
    client = TestClient(create_app(store=LocalActionStore(), secret=SECRET, now=NOW))
    proposal = _proposal()
    response = client.post(
        "/actions/create_monitor_task",
        json={"proposal": proposal, "approval_token": _token(proposal)},
    )
    assert response.status_code == 200
    assert response.json()["dry_run"] is True
    assert response.json()["task_id"] == "task-fc-1"

