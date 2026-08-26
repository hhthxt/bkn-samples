#!/usr/bin/env python3
"""Resolve the published Function Toolbox in the current OpenBKN environment.

The sample carries the portable toolbox name, never a platform UUID. The
resolved ID is written only to a local ignored deployment-state file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from register_native_function_toolbox import _call
from toolbox_resolution import resolve_published_toolbox


def resolve(*, box_name: str, required_tool_count: int | None = 13) -> dict[str, object]:
    boxes = _call(["toolbox", "list", "--keyword", box_name, "--limit", "100"])
    candidates = boxes.get("data", boxes.get("entries", []))
    exact = next(
        (item for item in candidates if item.get("box_name") == box_name), None
    )
    if not exact:
        raise RuntimeError(f"published toolbox not found: {box_name}")
    box_id = exact.get("box_id") or exact.get("id")
    tools = _call(["tool", "list", "--toolbox", str(box_id), "--all"])
    return resolve_published_toolbox(
        boxes,
        tools,
        name=box_name,
        required_tool_count=required_tool_count,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--box-name", default="供应链计算函数工具箱")
    parser.add_argument("--required-tool-count", type=int, default=13)
    parser.add_argument("--write-state", action="store_true")
    args = parser.parse_args()
    result = resolve(box_name=args.box_name, required_tool_count=args.required_tool_count)
    if args.write_state:
        state_path = Path(__file__).resolve().parent / ".deployment" / "function-toolbox.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result = {**result, "state_file": str(state_path)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
