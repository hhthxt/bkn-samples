"""Print a portable binding plan; platform writes require explicit --apply."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapping", default="mapping/action_dataset_map.yaml")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    mapping = Path(__file__).resolve().parent / args.mapping
    print(json.dumps({"mapping": str(mapping), "mode": "apply" if args.apply else "dry-run"}, indent=2))
    if not args.apply:
        print(mapping.read_text())


if __name__ == "__main__":
    main()
