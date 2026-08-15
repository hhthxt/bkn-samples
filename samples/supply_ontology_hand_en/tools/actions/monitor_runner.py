from datetime import datetime, timezone
from typing import Any

from .monitor_task import _items
from .store import LocalActionStore


class MonitorRunner:
    def __init__(self, store: LocalActionStore):
        self.store = store

    def run_once(self, refreshed_results: dict[str, dict[str, Any]], *, now: datetime | None = None) -> dict[str, Any]:
        checked_at = (now or datetime.now(timezone.utc)).isoformat()
        updated = 0
        errors = []
        for task_id, result in refreshed_results.items():
            task = self.store.tasks.get(task_id)
            if not task or task.get("task_status") in {"completed", "closed"}:
                continue
            try:
                status = "ready" if result.get("can_deliver_on_time") else "risk"
                task.update({"task_status": status, "kitting_status": status, "can_deliver_on_time": bool(result.get("can_deliver_on_time")), "max_delay_days": int(result.get("max_delay_days") or 0), "snapshot_id": result.get("snapshot_id") or task.get("snapshot_id"), "last_checked_at": checked_at})
                self.store.items[task_id] = _items(task, result)
                updated += 1
            except (TypeError, ValueError, KeyError) as exc:
                errors.append({"task_id": task_id, "error": str(exc)})
        return {"updated": updated, "errors": errors, "checked_at": checked_at, "dry_run": True}
