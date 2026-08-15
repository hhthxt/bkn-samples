"""Local, dry-run-only Action Gateway for the partner kit."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException

from actions.approval import ApprovalError, ApprovalExpired, ApprovalReplay, ApprovalRequired
from actions.monitor_task import close_monitor_task, create_monitor_task
from actions.pr_decision import create_pr_decision
from actions.store import LocalActionStore


ACTION_TYPES = ("close_monitor_task", "create_monitor_task", "create_pr_decision")


def create_app(*, store: LocalActionStore | None = None, secret: str | None = None, now: datetime | None = None) -> FastAPI:
    app = FastAPI(title="Supply Chain Action Gateway", version="0.1.0")
    action_store = store or LocalActionStore()
    approval_secret = secret if secret is not None else os.getenv("SUPPLY_ACTION_APPROVAL_SECRET", "")
    # Keep deterministic clock injection for tests, but do not freeze the
    # approval window for a long-running gateway in production.
    clock = lambda: now if now is not None else datetime.now(timezone.utc)

    @app.get("/health", include_in_schema=False)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready", include_in_schema=False)
    def ready() -> dict[str, Any]:
        if not approval_secret:
            raise HTTPException(status_code=503, detail={"error": "approval_secret_missing"})
        return {"status": "ok", "dry_run": True, "actions": list(ACTION_TYPES)}

    def execute(action: str, body: dict[str, Any]) -> dict[str, Any]:
        if not approval_secret:
            raise HTTPException(status_code=503, detail={"error": "approval_secret_missing"})
        proposal = body.get("proposal")
        if not isinstance(proposal, dict):
            raise HTTPException(status_code=422, detail={"error": "proposal_required"})
        token = body.get("approval_token")
        if not token:
            raise HTTPException(status_code=401, detail={"error": "approval_required"})
        try:
            if action == "create_monitor_task":
                return create_monitor_task(proposal, token, store=action_store, secret=approval_secret, now=clock())
            if action == "create_pr_decision":
                return create_pr_decision(proposal, token, store=action_store, secret=approval_secret, now=clock())
            return close_monitor_task(proposal, token, store=action_store, secret=approval_secret, now=clock())
        except ApprovalRequired as exc:
            raise HTTPException(status_code=401, detail={"error": "approval_required", "message": str(exc)}) from exc
        except ApprovalExpired as exc:
            raise HTTPException(status_code=401, detail={"error": "approval_expired", "message": str(exc)}) from exc
        except ApprovalReplay as exc:
            raise HTTPException(status_code=409, detail={"error": "approval_replay", "message": str(exc)}) from exc
        except ApprovalError as exc:
            raise HTTPException(status_code=403, detail={"error": "approval_invalid", "message": str(exc)}) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"error": "invalid_action", "message": str(exc)}) from exc

    @app.post("/actions/create_monitor_task")
    def create_monitor(body: dict[str, Any]) -> dict[str, Any]:
        return execute("create_monitor_task", body)

    @app.post("/actions/create_pr_decision")
    def create_pr(body: dict[str, Any]) -> dict[str, Any]:
        return execute("create_pr_decision", body)

    @app.post("/actions/close_monitor_task")
    def close_monitor(body: dict[str, Any]) -> dict[str, Any]:
        return execute("close_monitor_task", body)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("action_gateway:app", host="127.0.0.1", port=8766)
