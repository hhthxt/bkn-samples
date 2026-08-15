"""Bind Action Dataset tables to KN object types through OpenBKN."""

import argparse
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import yaml


def build_bindings(mapping: dict, *, kn_id: str, schema: str) -> list[dict]:
    result = []
    for item in mapping.get("bindings", []):
        dataset = str(item["dataset"])
        if dataset.startswith("${ACTION_DATASET_SCHEMA}."):
            dataset = f"{schema}.{dataset.split('.', 1)[1]}"
        elif "." not in dataset:
            dataset = f"{schema}.{dataset}"
        result.append({"kn_id": kn_id, "object_type_id": item["object_type_id"], "dataset": dataset})
    return result


def run_cmd(args: list[str]) -> str:
    proc = subprocess.run(args, capture_output=True, text=True, check=False)
    if proc.returncode:
        raise RuntimeError((proc.stderr or proc.stdout).strip())
    return proc.stdout


def parse_json(raw: str):
    data = json.loads(raw)
    if isinstance(data, dict) and isinstance(data.get("entries"), list):
        return data["entries"][0]
    return data


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == root.name:
        return root.parent / path
    return root / path


def run_bind(config: dict, mapping: dict, *, dry_run: bool, run_cmd=run_cmd) -> dict:
    kn_id = (config.get("openbkn") or {}).get("kn_id")
    if not kn_id:
        raise ValueError("openbkn.kn_id is required")
    schema = (config.get("database") or {}).get("schema") or "public"
    bindings = build_bindings(mapping, kn_id=kn_id, schema=schema)
    report = {"kn_id": kn_id, "dry_run": dry_run, "ok": True, "bindings": bindings}
    if dry_run:
        return report
    for binding in bindings:
        ot_id = binding["object_type_id"]
        current = parse_json(run_cmd(["openbkn", "--json", "bkn", "object-type", "get", kn_id, ot_id]))
        body = copy.deepcopy(current)
        body["data_source"] = {"type": "dataset", "id": binding["dataset"]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as tmp:
            json.dump(body, tmp, ensure_ascii=False)
            body_path = tmp.name
        try:
            run_cmd(["openbkn", "--json", "bkn", "object-type", "update", kn_id, ot_id, "--body-file", body_path])
        finally:
            Path(body_path).unlink(missing_ok=True)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapping", default="mapping/action_dataset_map.yaml")
    parser.add_argument("--config", default="config.poc.yaml")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    mapping = resolve_path(root, args.mapping)
    config = yaml.safe_load(resolve_path(root, args.config).read_text(encoding="utf-8"))
    payload = yaml.safe_load(mapping.read_text(encoding="utf-8"))
    report = run_bind(config, payload, dry_run=not args.apply)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
