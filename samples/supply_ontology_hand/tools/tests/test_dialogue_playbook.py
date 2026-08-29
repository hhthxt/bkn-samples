from datetime import datetime, timezone
from pathlib import Path

import pytest

from actions.approval import ApprovalAuthority, ApprovalRequired
from actions.store import LocalActionStore
from dialogue.playbook import ConversationPlaybook


PACK = Path(__file__).parents[2]
NOW = datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc)
SECRET = "dialogue-test-secret"


def test_dialogue_collects_context_before_running_the_story():
    playbook = ConversationPlaybook(PACK / "data", now=NOW)

    first = playbook.start()
    assert first["state"] == "collecting_context"
    assert "product" in first["missing_fields"]
    assert "business_date" not in first["missing_fields"]

    response = playbook.handle({"type": "provide_context", "product": "U00-000080"})
    assert response["state"] == "collecting_context"
    assert "forecast_id" in response["missing_fields"]

    response = playbook.handle(
        {
            "type": "provide_context",
            "forecast_id": "0000023181",
            "demand_end": "2026-05-31",
            "demand_qty": 3000,
            "substitute_enabled": False,
        }
    )
    assert response["state"] == "awaiting_s1_review"
    assert [step["id"] for step in response["visible_steps"]] == ["s1"]


def test_dialogue_reveals_story_steps_and_waits_for_human_action_confirmation():
    playbook = ConversationPlaybook(PACK / "data", now=NOW)
    playbook.start()
    response = playbook.handle(
        {
            "type": "provide_context",
            "product": "U00-000080",
            "forecast_id": "0000023181",
            "demand_end": "2026-05-31",
            "demand_qty": 3000,
            "business_date": "2026-08-25",
            "substitute_enabled": False,
        }
    )
    response = playbook.handle({"type": "continue", "step": "s2"})
    assert response["state"] == "awaiting_s3_or_action"
    assert [step["id"] for step in response["visible_steps"]] == ["s1", "s2"]

    response = playbook.handle({"type": "propose_action", "action": "create_monitor_task"})
    assert response["state"] == "awaiting_human_confirmation"
    assert response["action"]["status"] == "proposed"
    assert playbook.store.tasks == {}


def test_dialogue_never_executes_action_without_approval_token():
    playbook = ConversationPlaybook(PACK / "data", store=LocalActionStore(), now=NOW)
    playbook.start()
    playbook.handle(
        {
            "type": "provide_context",
            "product": "U00-000080",
            "forecast_id": "0000023181",
            "demand_end": "2026-05-31",
            "demand_qty": 3000,
            "business_date": "2026-08-25",
            "substitute_enabled": False,
        }
    )
    playbook.handle({"type": "continue", "step": "s2"})
    playbook.handle({"type": "propose_action", "action": "create_monitor_task"})
    with pytest.raises(ApprovalRequired):
        playbook.handle({"type": "confirm_action", "action": "create_monitor_task"})
    assert playbook.store.tasks == {}


def test_dialogue_executes_only_the_approved_pending_action():
    playbook = ConversationPlaybook(PACK / "data", store=LocalActionStore(), now=NOW, approval_secret=SECRET)
    playbook.start()
    playbook.handle(
        {
            "type": "provide_context",
            "product": "U00-000080",
            "forecast_id": "0000023181",
            "demand_end": "2026-05-31",
            "demand_qty": 3000,
            "business_date": "2026-08-25",
            "substitute_enabled": False,
        }
    )
    playbook.handle({"type": "continue", "step": "s2"})
    playbook.handle({"type": "propose_action", "action": "create_monitor_task"})
    proposal = playbook.pending_actions["create_monitor_task"]
    token = ApprovalAuthority(SECRET).issue(
        proposal,
        action_type="create_monitor_task",
        interaction_id=proposal["interaction_id"],
        approver="planner-01",
        idempotency_key=proposal["idempotency_key"],
        now=NOW,
    )
    response = playbook.handle({"type": "confirm_action", "action": "create_monitor_task", "approval_token": token})
    assert response["state"] == "action_completed"
    assert response["result"]["dry_run"] is True
    assert playbook.store.tasks
