"""Bootstrap Action Dataset tables and bind them to the sample KN."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from bind_action_datasets import discover_catalog, run_bind
from setup_action_datasets import apply_ddl, interactive_connection


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == root.name:
        return root.parent / path
    return root / path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create and bind Action Dataset tables")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--mapping", default="mapping/action_dataset_map.yaml")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parent
    config = yaml.safe_load(resolve_path(root, args.config).read_text(encoding="utf-8"))
    mapping = yaml.safe_load(resolve_path(root, args.mapping).read_text(encoding="utf-8"))
    if not (args.apply or args.interactive):
        print(json.dumps({"mode": "dry-run", "bind": run_bind(config, mapping, dry_run=True)}, ensure_ascii=False, indent=2))
        return 0
    connection = interactive_connection()
    try:
        ddl = apply_ddl(connection, schema=(config.get("database") or {}).get("schema") or "public")
    finally:
        connection.close()
    discover_catalog((config.get("vega") or {}).get("catalog_id"))
    bind = run_bind(config, mapping, dry_run=False)
    print(json.dumps({"mode": "apply", "ddl": ddl, "bind": bind}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
