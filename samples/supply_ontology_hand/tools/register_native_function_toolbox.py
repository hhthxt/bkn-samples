#!/usr/bin/env python3
"""Register the sample's single native Function Tool through OpenBKN Foundry.

This is the default third-party path: it needs only an authenticated OpenBKN
CLI profile.  No function server, container, host name, or service URL exists
in this flow.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from typing import Any

from native_function_bundle import build_native_function_code


API = "/api/agent-operator-integration/v1"
TOOL_NAME = "supply_chain_compute"


def _call(args: list[str]) -> Any:
    completed = subprocess.run(
        ["openbkn", "--json", *args], check=False, capture_output=True, text=True
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(detail or f"openbkn 调用失败（退出码 {completed.returncode}）")
    return json.loads(completed.stdout)


def _tool_input() -> dict[str, Any]:
    return {
        "name": TOOL_NAME,
        "description": "供应链纯计算函数。operation 指定计算口径；parameters 含业务参数和受管 resolved_context。函数不查数据库。",
        "script_type": "python",
        "code": build_native_function_code(),
        "inputs": [
            {
                "name": "operation",
                "type": "string",
                "required": True,
                "description": "bom_list、total_sellable、backward_plan 等受支持计算操作。",
            },
            {
                "name": "parameters",
                "type": "object",
                "required": True,
                "description": "该 operation 的参数，必须包含 resolved_context。",
            },
        ],
        "outputs": [
            {
                "name": "result",
                "type": "object",
                "required": True,
                "description": "计算结果和 snapshot_meta。",
            }
        ],
    }


def _find_exact_box(name: str) -> dict[str, Any] | None:
    listing = _call(["toolbox", "list", "--keyword", name, "--limit", "100"])
    for item in listing.get("data", listing.get("entries", [])):
        if item.get("box_name") == name:
            return item
    return None


def _find_tool(box_id: str) -> dict[str, Any] | None:
    listing = _call(["tool", "list", "--toolbox", box_id, "--all"])
    for item in listing.get("tools", []):
        if item.get("name") == TOOL_NAME:
            return item
    return None


def run(*, box_name: str, apply: bool) -> dict[str, Any]:
    tool_input = _tool_input()
    preview = {
        "mode": "apply" if apply else "dry_run",
        "box_name": box_name,
        "metadata_type": "function",
        "tool_name": TOOL_NAME,
        "entrypoint": "handler(event)",
        "needs_external_service": False,
        "code_bytes": len(tool_input["code"].encode("utf-8")),
    }
    if not apply:
        return preview

    box = _find_exact_box(box_name)
    if box is None:
        box = _call(
            [
                "call",
                f"{API}/tool-box",
                "-X",
                "POST",
                "-d",
                json.dumps(
                    {
                        "box_name": box_name,
                        "box_desc": "supply_ontology_hand 原生供应链计算函数；由 OpenBKN Function Runtime 执行。",
                        "box_category": "data_process",
                        "metadata_type": "function",
                        "source": "custom",
                    },
                    ensure_ascii=False,
                ),
            ]
        )
    box_id = box["box_id"]
    tool = _find_tool(box_id)
    if tool is None:
        created = _call(
            [
                "call",
                f"{API}/tool-box/{box_id}/tool",
                "-X",
                "POST",
                "-d",
                json.dumps({"metadata_type": "function", "function_input": tool_input}, ensure_ascii=False),
            ]
        )
        tool_id = created["success_ids"][0]
        _call(["tool", "enable", "--toolbox", box_id, tool_id])
    else:
        tool_id = tool["tool_id"]
        # Re-registering is intentionally idempotent: keep the stable tool ID
        # that an Agent/manual deployment recorded, while replacing the
        # immutable Function Runtime bundle with the current sample version.
        _call(
            [
                "call",
                f"{API}/tool-box/{box_id}/tool/{tool_id}",
                "-X",
                "POST",
                "-d",
                json.dumps(
                    {
                        "name": TOOL_NAME,
                        "description": tool_input["description"],
                        "metadata_type": "function",
                        "function_input": tool_input,
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        if tool.get("status") != "enabled":
            _call(["tool", "enable", "--toolbox", box_id, tool_id])
    if box.get("status") != "published":
        _call(["toolbox", "publish", box_id])
    return {**preview, "box_id": box_id, "tool_id": tool_id}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--box-name", default="供应链原生计算函数")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(box_name=args.box_name, apply=args.apply), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
