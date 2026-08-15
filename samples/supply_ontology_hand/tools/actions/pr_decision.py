from __future__ import annotations
import hashlib
from datetime import datetime
from typing import Any
from .approval import ApprovalAuthority, ApprovalReplay
from .store import LocalActionStore

def create_pr_decision(proposal: dict[str, Any], token: str | None, *, store: LocalActionStore, secret: str, now: datetime) -> dict[str, Any]:
    required = ("decision_batch_id", "forecast_id", "product_code", "material_code", "recommended_qty", "snapshot_id", "interaction_id", "idempotency_key")
    missing = [key for key in required if not str(proposal.get(key) or "").strip()]
    if missing: raise ValueError(f"missing proposal fields: {', '.join(missing)}")
    if proposal["idempotency_key"] in store.used_idempotency: raise ApprovalReplay("idempotency key already used")
    approval = ApprovalAuthority(secret).verify(token, proposal, action_type="create_pr_decision", interaction_id=proposal["interaction_id"], idempotency_key=proposal["idempotency_key"], now=now)
    store.mark_idempotency(proposal["idempotency_key"])
    decision_id = proposal.get("decision_id") or "decision_" + hashlib.sha256(proposal["idempotency_key"].encode()).hexdigest()[:16]
    record = {"decision_id": decision_id, "decision_batch_id": proposal["decision_batch_id"], "forecast_id": proposal["forecast_id"], "product_code": proposal["product_code"], "material_code": proposal["material_code"], "recommended_qty": float(proposal["recommended_qty"]), "required_date": proposal.get("required_date"), "warehouse_scope": proposal.get("warehouse_scope", "ALL"), "substitute_enabled": bool(proposal.get("substitute_enabled", False)), "reason_code": proposal.get("reason_code", "shortage"), "snapshot_id": proposal["snapshot_id"], "interaction_id": proposal["interaction_id"], "status": "approved", "approved_by": approval["approver"], "approved_at": approval["issued_at"], "idempotency_key": proposal["idempotency_key"]}
    store.save_decision(record)
    return {"status": "approved", "decision_id": decision_id, "record": record, "dry_run": True}
