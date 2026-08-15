#!/usr/bin/env python3
"""Encode a managed resolved_context for the native Function Runtime."""

from __future__ import annotations

import argparse
import base64
import json
import zlib
from pathlib import Path


def encode(payload: object) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(zlib.compress(raw)).decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="resolved_context JSON 文件")
    parser.add_argument("--wrap", action="store_true", help="输出 parameters 字段对象")
    args = parser.parse_args()
    with args.input.open(encoding="utf-8") as handle:
        packed = encode(json.load(handle))
    print(json.dumps({"resolved_context_compressed": packed} if args.wrap else packed, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
