"""Step 2: import experience-pack KN JSON via openbkn CLI."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_JSON = _SCRIPT_DIR.parent / "kn" / "supply_ontology_hand.json"
_IMPORT_PATH = "/api/ontology-manager/v1/knowledge-networks"
_UI_FALLBACK_MSG = "请按说明书步骤 2 UI 导入知识网络"


def run_cmd(args: list[str]) -> str:
    proc = subprocess.run(args, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(
            f"openbkn failed ({proc.returncode}): {' '.join(args)}\n{detail}"
        )
    return proc.stdout


def import_kn(json_path: Path, *, dry_run: bool = False) -> dict:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    kn_id = payload.get("id")
    kn_name = payload.get("name")
    if not kn_id or not kn_name:
        raise ValueError(f"KN JSON missing id/name: {json_path}")

    report = {
        "json_path": str(json_path),
        "kn_id": kn_id,
        "kn_name": kn_name,
        "dry_run": dry_run,
    }

    if dry_run:
        report["action"] = "would_import"
        return report

    body = json.dumps(payload, ensure_ascii=False)
    raw = run_cmd(["openbkn", "--json", "call", "-X", "POST", _IMPORT_PATH, "-d", body])
    try:
        report["import_response"] = json.loads(raw)
    except json.JSONDecodeError:
        report["import_response_raw"] = raw

    got = json.loads(run_cmd(["openbkn", "--json", "bkn", "get", kn_id]))
    report["verified"] = got.get("id") == kn_id and got.get("name") == kn_name
    if not report["verified"]:
        raise RuntimeError(f"import verification failed for {kn_id}: {got!r}")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import KN JSON (step 2) via openbkn call")
    parser.add_argument(
        "--json",
        default=str(_DEFAULT_JSON),
        help="Path to KN export JSON (default: ../kn/supply_ontology_hand.json)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Only print kn id/name")
    args = parser.parse_args(argv)

    try:
        report = import_kn(Path(args.json), dry_run=args.dry_run)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (RuntimeError, json.JSONDecodeError, OSError, ValueError) as exc:
        print(_UI_FALLBACK_MSG, file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
