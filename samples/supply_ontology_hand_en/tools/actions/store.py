from copy import deepcopy
from typing import Any

class LocalActionStore:
    def __init__(self):
        self.decisions: dict[str, dict[str, Any]] = {}
        self.tasks: dict[str, dict[str, Any]] = {}
        self.items: dict[str, list[dict[str, Any]]] = {}
        self.used_idempotency: set[str] = set()
    def mark_idempotency(self, key: str) -> None:
        if key in self.used_idempotency: raise ValueError(f"idempotency key already used: {key}")
        self.used_idempotency.add(key)
    def save_decision(self, value: dict[str, Any]) -> None: self.decisions[value["decision_id"]] = deepcopy(value)
    def save_task(self, task: dict[str, Any], items: list[dict[str, Any]]) -> None:
        self.tasks[task["task_id"]] = deepcopy(task)
        self.items[task["task_id"]] = deepcopy(items)
