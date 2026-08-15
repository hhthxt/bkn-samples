#!/usr/bin/env python3
"""Export the function service OpenAPI document for toolbox registration."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from fn_service import app


PACK = Path(__file__).resolve().parent.parent
OUTPUT = PACK / "docs" / "payloads" / "functions-openapi.json"


def _remove_null_schemas(value: Any) -> Any:
    if isinstance(value, list):
        return [_remove_null_schemas(item) for item in value]
    if not isinstance(value, dict):
        return value

    cleaned = {
        key: _remove_null_schemas(item)
        for key, item in value.items()
        if key != "anyOf"
    }
    if "anyOf" not in value:
        return cleaned

    branches = [
        _remove_null_schemas(item)
        for item in value["anyOf"]
        if not (isinstance(item, dict) and item.get("type") == "null")
    ]
    if len(branches) == 1:
        return {**branches[0], **cleaned}
    cleaned["anyOf"] = branches
    return cleaned


def build_toolbox_openapi() -> dict[str, Any]:
    spec = _remove_null_schemas(deepcopy(app.openapi()))
    spec["openapi"] = "3.0.3"
    spec["servers"] = [{"url": "http://host.docker.internal:8765"}]
    return spec


def main() -> int:
    OUTPUT.write_text(
        json.dumps(build_toolbox_openapi(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
