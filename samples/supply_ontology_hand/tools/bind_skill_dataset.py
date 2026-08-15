"""Bind the dataset-backed `skills` object type to a discovered Resource."""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import tempfile
from pathlib import Path


def build_binding(kn_id: str, object_type_id: str, resource_id: str) -> dict:
    return {"kn_id": kn_id, "object_type_id": object_type_id, "data_source": {"type": "resource", "id": resource_id}}


def run(args: list[str]) -> dict:
    proc = subprocess.run(["openbkn", "--json", *args], check=False, capture_output=True, text=True)
    if proc.returncode:
        raise RuntimeError((proc.stderr or proc.stdout).strip())
    return json.loads(proc.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kn-id", default="supply_ontology_hand")
    parser.add_argument("--catalog-id", required=True)
    parser.add_argument("--resource-name", default="public.skills")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    found = run(["resource", "find", "--catalog-id", args.catalog_id, "--name", args.resource_name, "--exact"])
    entries = found if isinstance(found, list) else found.get("entries", [])
    if len(entries) != 1:
        raise SystemExit(f"Expected one Resource named {args.resource_name}, found {len(entries)}. Run Catalog Discover first.")
    resource_id = entries[0]["id"]
    binding = build_binding(args.kn_id, "skills", resource_id)
    print(json.dumps(binding, ensure_ascii=False, indent=2))
    if not args.apply:
        return
    current = run(["bkn", "object-type", "get", args.kn_id, "skills"])
    if isinstance(current, dict) and isinstance(current.get("entries"), list):
        current = current["entries"][0]
    body = copy.deepcopy(current)
    body["data_source"] = binding["data_source"]
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
        json.dump(body, handle, ensure_ascii=False)
        body_path = Path(handle.name)
    try:
        run(["bkn", "object-type", "update", args.kn_id, "skills", "--body-file", str(body_path)])
    finally:
        body_path.unlink(missing_ok=True)
    print(json.dumps(run(["bkn", "object-type", "get", args.kn_id, "skills"]), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
