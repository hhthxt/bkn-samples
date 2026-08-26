"""Pure contract helper for Agent-orchestrated Toolbox calls.

This module validates and packages data already retrieved by the Agent. It does
not query a data source, persist trace state, calculate business results, or
execute Actions.
"""

from __future__ import annotations

from copy import deepcopy
from collections.abc import Mapping
from datetime import date

from context.operation_contracts import required_datasets


BACKWARD_PLAN_PARAMETERS = frozenset(
    {
        "product_query",
        "forecast_id",
        "demand_end",
        "demand_qty",
        "substitute_enabled",
    }
)


def _require_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    return value


def build_toolbox_request(
    operation_id: str,
    *,
    bkn_context: Mapping[str, object],
    resolved_context: Mapping[str, object],
    parameters: Mapping[str, object],
) -> dict[str, object]:
    """Build a deterministic Toolbox request from Agent-owned context."""

    required = required_datasets(operation_id)
    trace = _require_mapping(bkn_context, "bkn_context")
    for field in ("conversation_id", "interaction_id"):
        if not trace.get(field):
            raise ValueError(f"bkn_context.{field} is required")

    context = _require_mapping(resolved_context, "resolved_context")
    if context.get("source") != "openbkn_context_loader":
        raise ValueError(
            "resolved_context.source must be openbkn_context_loader for online Toolbox calls"
        )
    rows = _require_mapping(context.get("rows"), "resolved_context.rows")
    receipts = _require_mapping(context.get("receipts"), "resolved_context.receipts")
    missing_rows = sorted(name for name in required if not rows.get(name))
    missing_receipts = sorted(
        name
        for name in required
        if not isinstance(receipts.get(name), Mapping)
        or not str(receipts[name].get("receipt_id") or "").strip()
    )
    if missing_rows:
        raise ValueError(f"resolved_context.rows missing: {', '.join(missing_rows)}")
    if missing_receipts:
        raise ValueError(
            f"resolved_context.receipts missing: {', '.join(missing_receipts)}"
        )

    args = _require_mapping(parameters, "parameters")
    if operation_id == "backward_plan":
        missing = sorted(name for name in BACKWARD_PLAN_PARAMETERS if name not in args)
        if missing:
            raise ValueError(f"parameters missing: {', '.join(missing)}")
        if not isinstance(args["substitute_enabled"], bool):
            raise ValueError("parameters.substitute_enabled must be boolean")
        try:
            date.fromisoformat(str(args["demand_end"]))
        except ValueError as exc:
            raise ValueError("parameters.demand_end must be YYYY-MM-DD") from exc

    return {
        "execution_mode": "agent_orchestrated",
        "operation_id": operation_id,
        "bkn_context": deepcopy(dict(trace)),
        "resolved_context": deepcopy(dict(context)),
        "arguments": deepcopy(dict(args)),
    }
