"""Strict release gate for the real online BKN path (MCP -> Toolbox -> Trace)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class OnlineAcceptanceError(ValueError):
    """Evidence is insufficient for publishing the online A path."""


def _value(row: Mapping[str, Any], field: str) -> Any:
    current: Any = row
    for part in field.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def _matches(row: Mapping[str, Any], condition: Mapping[str, Any]) -> bool:
    operator = str(condition.get("operator") or condition.get("operation") or "eq").lower()
    if operator in {"and", "&&"}:
        children = condition.get("sub_conditions") or condition.get("conditions")
        return isinstance(children, Sequence) and all(
            isinstance(child, Mapping) and _matches(row, child) for child in children
        )
    field = str(condition.get("field") or "").strip()
    if not field:
        return False
    actual = _value(row, field)
    expected = condition.get("value")
    if operator in {"eq", "=", "=="}:
        return actual == expected
    if operator in {"neq", "!=", "ne"}:
        return actual != expected
    if operator == "in":
        return isinstance(expected, Sequence) and not isinstance(expected, (str, bytes)) and actual in expected
    raise OnlineAcceptanceError(f"unsupported query condition operator: {operator}")


def _validate_query(query: Mapping[str, Any], conversation_id: str, interaction_id: str) -> None:
    dataset = str(query.get("dataset") or "").strip()
    rows = query.get("rows")
    condition = query.get("condition")
    receipt = query.get("bkn_receipt")
    if not dataset or not isinstance(rows, list) or not isinstance(condition, Mapping):
        raise OnlineAcceptanceError("query evidence requires dataset, condition and rows")
    if not all(isinstance(row, Mapping) and _matches(row, condition) for row in rows):
        raise OnlineAcceptanceError(f"Context Loader result violates exact condition for {dataset}")
    if not isinstance(receipt, Mapping) or not str(receipt.get("receipt_id") or "").strip():
        raise OnlineAcceptanceError(f"valid bkn_receipt required for {dataset}")
    if str(receipt.get("dataset") or "") != dataset:
        raise OnlineAcceptanceError(f"bkn_receipt dataset mismatch for {dataset}")
    if str(receipt.get("interaction_id") or "") != interaction_id:
        raise OnlineAcceptanceError(f"bkn_receipt interaction mismatch for {dataset}")
    if receipt.get("row_count") != len(rows):
        raise OnlineAcceptanceError(f"bkn_receipt row_count mismatch for {dataset}")


def validate_path_a_evidence(evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one real MCP Interaction acceptance evidence document.

    Offline answers are intentionally not accepted as a degraded success.
    """

    if not isinstance(evidence, Mapping) or evidence.get("path") != "A":
        raise OnlineAcceptanceError("path A evidence is required")
    if evidence.get("status") != "passed" or evidence.get("offline_fallback"):
        raise OnlineAcceptanceError("path A is blocked until real online evidence passes")
    conversation_id = str(evidence.get("conversation_id") or "")
    interaction_id = str(evidence.get("interaction_id") or "")
    if not conversation_id or not interaction_id:
        raise OnlineAcceptanceError("conversation_id and interaction_id are required")
    toolbox = evidence.get("toolbox")
    if not isinstance(toolbox, Mapping) or toolbox.get("status") != "published":
        raise OnlineAcceptanceError("published toolbox evidence is required")
    if not toolbox.get("box_id") or toolbox.get("enabled_tool_count") != 13:
        raise OnlineAcceptanceError("current published toolbox with 13 enabled tools is required")
    queries = evidence.get("queries")
    if not isinstance(queries, list) or not queries:
        raise OnlineAcceptanceError("Context Loader query evidence is required")
    for query in queries:
        if not isinstance(query, Mapping):
            raise OnlineAcceptanceError("query evidence must be an object")
        _validate_query(query, conversation_id, interaction_id)
    tool_call = evidence.get("tool_call")
    if not isinstance(tool_call, Mapping) or tool_call.get("status_code") not in {200, 201}:
        raise OnlineAcceptanceError("published toolbox read-only function call is required")
    trace = evidence.get("trace")
    if not isinstance(trace, Mapping) or trace.get("reread") is not True:
        raise OnlineAcceptanceError("trace reread evidence is required")
    if trace.get("conversation_id") != conversation_id or trace.get("interaction_id") != interaction_id:
        raise OnlineAcceptanceError("trace identifiers do not match MCP interaction")
    return {"status": "passed", "path": "A", "box_id": toolbox["box_id"]}
