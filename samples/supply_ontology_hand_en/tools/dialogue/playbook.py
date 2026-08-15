from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from actions.monitor_task import close_monitor_task, create_monitor_task
from actions.pr_decision import create_pr_decision
from actions.store import LocalActionStore
from scenario.runner import FulfillmentCommitmentRunner


REQUIRED_CONTEXT = ("product", "forecast_id", "demand_end", "demand_qty", "substitute_enabled")


class ConversationPlaybook:
    """Stateful adapter: Agent supplies structured turns; human confirms Actions."""

    def __init__(self, data_dir: str | Path, *, store: LocalActionStore | None = None, approval_secret: str = "local-dialogue-secret", now: datetime | None = None):
        self.data_dir = Path(data_dir)
        self.runner = FulfillmentCommitmentRunner(self.data_dir)
        self.store = store or LocalActionStore()
        self.approval_secret = approval_secret
        self.now = now or datetime.now(timezone.utc)
        self.context: dict[str, Any] = {}
        self.report: dict[str, Any] | None = None
        self.pending_actions: dict[str, dict[str, Any]] = {}
        self.state = "new"

    def start(self) -> dict[str, Any]:
        self.context = {}
        self.report = None
        self.pending_actions = {}
        self.state = "collecting_context"
        return self._context_response()

    def handle(self, event: dict[str, Any]) -> dict[str, Any]:
        event_type = event.get("type")
        if event_type == "provide_context":
            self.context.update({key: value for key, value in event.items() if key != "type"})
            missing = self._missing()
            if missing:
                self.state = "collecting_context"
                return self._context_response()
            self.report = self.runner.run(**{key: self.context[key] for key in REQUIRED_CONTEXT})
            self.state = "awaiting_s1_review"
            return self._story_response(["s1"], "请先审阅倒排和齐套证据；确认后继续查看可售能力。")
        if event_type == "continue":
            return self._continue(event)
        if event_type == "propose_action":
            return self._propose(event.get("action"))
        if event_type == "confirm_action":
            return self._confirm(event.get("action"), event.get("approval_token"))
        raise ValueError(f"unsupported dialogue event: {event_type}")

    def _continue(self, event: dict[str, Any]) -> dict[str, Any]:
        if self.report is None:
            raise ValueError("context is required before continuing")
        step = event.get("step")
        if step == "s2" and self.state == "awaiting_s1_review":
            self.state = "awaiting_s3_or_action"
            return self._story_response(["s1", "s2"], "现在可以补充其他需求做 S3，或提出监控/采购决策建议。")
        if step == "s3" and self.state in {"awaiting_s3_or_action", "awaiting_s1_review"}:
            demands = event.get("demands")
            if not demands:
                raise ValueError("S3 requires at least two demands")
            self.report = self.runner.run(**{key: self.context[key] for key in REQUIRED_CONTEXT}, demands=demands)
            self.state = "awaiting_s3_or_action"
            return self._story_response(["s1", "s2", "s3"], "S3 已完成；请选择是否提出受控行动。")
        raise ValueError(f"step {step} is not available in state {self.state}")

    def _propose(self, action: str | None) -> dict[str, Any]:
        if self.report is None or action not in {"create_monitor_task", "create_pr_decision"}:
            raise ValueError("a completed story and supported action are required")
        if not any(item.get("action") == action for item in self.report.get("action_proposals", [])):
            raise ValueError(f"action is not supported by current evidence: {action}")
        proposal = self._proposal(action)
        self.pending_actions[action] = proposal
        self.state = "awaiting_human_confirmation"
        return {"state": self.state, "action": {"action": action, "status": "proposed", "proposal": proposal}, "prompt": "这是建议动作。请人工确认后再执行；未确认不会写入。"}

    def _confirm(self, action: str | None, token: str | None) -> dict[str, Any]:
        proposal = self.pending_actions.get(action or "")
        if proposal is None:
            raise ValueError("no pending action")
        if action == "create_monitor_task":
            result = create_monitor_task(proposal, token, store=self.store, secret=self.approval_secret, now=self.now)
        elif action == "create_pr_decision":
            result = create_pr_decision(proposal, token, store=self.store, secret=self.approval_secret, now=self.now)
        else:
            raise ValueError(f"unsupported action: {action}")
        self.state = "action_completed"
        return {"state": self.state, "result": result}

    def _proposal(self, action: str) -> dict[str, Any]:
        assert self.report is not None
        meta = self.report["snapshot_meta"]
        base = {"action_type": action, "interaction_id": meta["interaction_id"], "snapshot_id": meta["snapshot_id"], "forecast_id": self.context["forecast_id"], "product_code": self.context["product"], "idempotency_key": self._idempotency(action)}
        if action == "create_monitor_task":
            base.update({"task_id": "task_" + self.context["forecast_id"], "forecast_qty": self.context["demand_qty"], "demand_end": self.context["demand_end"], "s1_result": self.report["steps"][0]["result"]})
        else:
            gap = (self.report["steps"][0]["result"].get("gaps") or [{}])[0]
            base.update({"decision_batch_id": "batch_" + self.context["forecast_id"], "material_code": gap.get("material_code", ""), "recommended_qty": gap.get("shortage_qty", 0), "reason_code": "shortage"})
        return base

    def _idempotency(self, action: str) -> str:
        return "dialogue-" + hashlib.sha256(f"{action}|{self.context.get('forecast_id')}|{self.report['snapshot_meta']['input_digest']}".encode()).hexdigest()[:20]

    def _missing(self) -> list[str]:
        return [key for key in REQUIRED_CONTEXT if key not in self.context or self.context[key] in (None, "")]

    def _context_response(self) -> dict[str, Any]:
        missing = self._missing()
        return {"state": self.state, "missing_fields": missing, "prompt": "请补充产品、需求预测单、需求数量、截止日和替代料策略。"}

    def _story_response(self, ids: list[str], prompt: str) -> dict[str, Any]:
        assert self.report is not None
        steps = [step for step in self.report["steps"] if step["id"] in ids]
        return {"state": self.state, "visible_steps": steps, "snapshot_meta": self.report["snapshot_meta"], "prompt": prompt}


__all__ = ["ConversationPlaybook"]
