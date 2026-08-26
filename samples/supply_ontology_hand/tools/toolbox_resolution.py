"""Portable resolution of a published Function Toolbox deployment.

Sample contracts may name a toolbox, but must never carry an environment UUID.
This module is deliberately pure so it can be tested without platform access.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class ToolboxResolutionError(ValueError):
    """The requested published deployment cannot be used safely."""


def _items(payload: Mapping[str, Any], *keys: str) -> list[Mapping[str, Any]]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, Mapping)]
    return []


def _box_id(box: Mapping[str, Any]) -> str:
    value = box.get("box_id") or box.get("id")
    return str(value or "").strip()


def _version_key(box: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        str(box.get("version") or ""),
        str(box.get("updated_at") or ""),
        str(box.get("created_at") or ""),
    )


def resolve_published_toolbox(
    boxes_payload: Mapping[str, Any],
    tools_payload: Mapping[str, Any],
    *,
    name: str,
    required_tool_count: int | None = None,
    required_tool_names: set[str] | None = None,
) -> dict[str, Any]:
    """Resolve the current published box and validate its enabled tools.

    If a platform returns several versions, the highest platform version and
    then the newest update timestamp is selected. The returned ``box_id`` is
    runtime state only; callers must not commit it into the sample contract.
    """

    requested = name.strip()
    if not requested:
        raise ToolboxResolutionError("toolbox name is required")
    boxes = [
        box
        for box in _items(boxes_payload, "data", "entries", "items")
        if str(box.get("box_name") or box.get("name") or "").strip() == requested
        and str(box.get("status") or "").lower() == "published"
        and _box_id(box)
    ]
    if not boxes:
        raise ToolboxResolutionError(f"published toolbox not found: {requested}")
    box = sorted(boxes, key=_version_key, reverse=True)[0]

    tools = _items(tools_payload, "tools", "data", "entries", "items")
    disabled = [
        tool
        for tool in tools
        if str(tool.get("status") or "").lower() != "enabled"
    ]
    if disabled:
        raise ToolboxResolutionError(
            f"toolbox {requested} does not have all tools enabled; refuse online acceptance"
        )
    if required_tool_count is not None and len(tools) != required_tool_count:
        raise ToolboxResolutionError(
            f"toolbox {requested} expected {required_tool_count} enabled tools, found {len(tools)}"
        )
    if required_tool_names:
        actual = {str(tool.get("name") or tool.get("tool_name") or "") for tool in tools}
        missing = sorted(required_tool_names - actual)
        if missing:
            raise ToolboxResolutionError(f"toolbox tools missing: {', '.join(missing)}")

    return {
        "box_name": requested,
        "box_id": _box_id(box),
        "status": "published",
        "version": box.get("version"),
        "enabled_tool_count": len(tools),
        "tool_names": sorted(
            str(tool.get("name") or tool.get("tool_name") or "")
            for tool in tools
        ),
    }
