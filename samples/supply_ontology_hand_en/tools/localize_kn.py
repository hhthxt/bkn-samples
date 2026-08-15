"""Translate user-facing KN strings while preserving technical IDs."""

import json
import sys
from pathlib import Path

from localize_sample_data import translate


PRESERVE_FIELDS = {"id", "branch", "business_domain", "color", "icon", "type"}


def localize(value, field, cache):
    if isinstance(value, dict):
        return {key: localize(item, key, cache) for key, item in value.items()}
    if isinstance(value, list):
        return [localize(item, field, cache) for item in value]
    if isinstance(value, str) and field not in PRESERVE_FIELDS:
        return translate(value, cache)
    return value


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: localize_kn.py SOURCE_JSON TARGET_JSON")
    source, target = map(Path, sys.argv[1:])
    data = json.loads(source.read_text())
    target.write_text(json.dumps(localize(data, "", {}), ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
