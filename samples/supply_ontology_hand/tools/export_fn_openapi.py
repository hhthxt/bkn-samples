#!/usr/bin/env python3
"""Export the function service OpenAPI document for toolbox registration."""

from __future__ import annotations

import json
import argparse
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


def build_toolbox_openapi(service_url: str | None = None) -> dict[str, Any]:
    spec = _remove_null_schemas(deepcopy(app.openapi()))
    spec["openapi"] = "3.0.3"
    if service_url:
        spec["servers"] = [{"url": service_url.rstrip("/")}]
    else:
        spec.pop("servers", None)
    return spec


def main() -> int:
    parser = argparse.ArgumentParser(description="Export function Toolbox OpenAPI")
    parser.add_argument(
        "--service-url",
        help="POC-reachable function service URL; omit to leave endpoint configuration to Toolbox setup",
    )
    args = parser.parse_args()
    OUTPUT.write_text(
        json.dumps(build_toolbox_openapi(args.service_url), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
