from __future__ import annotations
import hashlib
from datetime import datetime
from typing import Any
from .approval import ApprovalAuthority
from .store import LocalActionStore

def create_monitor_task(proposal: dict[str, Any], token: str | None, *, store: LocalActionStore, secret: str, now: datetime) -> dict[str, Any]:
    required = ("task_id", "product_code", "forecast_id", "forecast_qty", "snapshot_id", "interaction_id", "idempotency_key", "s1_result")
    missing = [key for key in required if key not in proposal or proposal[key] in (None, "")]
    if missing: raise ValueError(f"missing proposal fields: {', '.join(missing)}")
    if any(task.get("forecast_id") == proposal["forecast_id"] and task.get("task_status") not in {"completed", "closed"} for task in store.tasks.values()): raise ValueError("open task already exists for forecast_id")
    approval = ApprovalAuthority(secret).verify(token, proposal, action_type="create_monitor_task", interaction_id=proposal["interaction_id"], idempotency_key=proposal["idempotency_key"], now=now)
    store.mark_idempotency(proposal["idempotency_key"])
    s1 = proposal["s1_result"]
    status = "ready" if s1.get("can_deliver_on_time") else "risk"
    task = {"task_id": proposal["task_id"], "product_code": proposal["product_code"], "forecast_id": proposal["forecast_id"], "forecast_qty": float(proposal["forecast_qty"]), "demand_end": proposal.get("demand_end"), "snapshot_id": proposal["snapshot_id"], "task_status": status, "kitting_status": status, "can_deliver_on_time": bool(s1.get("can_deliver_on_time")), "max_delay_days": int(s1.get("max_delay_days") or 0), "created_by": approval["approver"], "created_at": now.isoformat()}
    items = _items(task, s1)
    store.save_task(task, items)
    return {"task_id": task["task_id"], "task_status": status, "item_count": len(items), "dry_run": True}

def close_monitor_task(proposal: dict[str, Any], token: str | None, *, store: LocalActionStore, secret: str, now: datetime) -> dict[str, Any]:
    task = store.tasks.get(proposal.get("task_id"))
    if not task: raise ValueError("task not found")
    approval = ApprovalAuthority(secret).verify(token, proposal, action_type="close_monitor_task", interaction_id=proposal["interaction_id"], idempotency_key=proposal["idempotency_key"], now=now)
    store.mark_idempotency(proposal["idempotency_key"])
    task.update({"task_status": "closed", "closed_at": now.isoformat(), "close_reason": proposal["reason"], "closed_by": approval["approver"]})
    return {"task_id": task["task_id"], "task_status": "closed", "item_count": len(store.items.get(task["task_id"], [])), "dry_run": True}

def _items(task: dict[str, Any], s1: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for index, node in enumerate(s1.get("nodes") or []):
        evidence = node.get("evidence") or {}
        material = node.get("material_code", "")
        result.append({"item_id": "item_" + hashlib.sha256(f"{task['task_id']}|{material}|{index}".encode()).hexdigest()[:16], "task_id": task["task_id"], "material_code": material, "bom_level": int(node.get("bom_level") or 0), "required_date": node.get("end_date"), "available_qty": float(evidence.get("available_qty", 0) or 0), "in_transit_qty": float(evidence.get("in_transit_qty", 0) or 0), "net_shortage": float(evidence.get("shortage_qty", 0) or 0), "delay_class": node.get("delay_class") or "none", "supply_status": node.get("supply_status") or "unknown", "snapshot_id": task["snapshot_id"]})
    return result
