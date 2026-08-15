"""Prepare Action Dataset DDL; apply only when explicitly requested."""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=("postgres", "mysql"), default="postgres")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    sql = Path(__file__).resolve().parents[1] / "datasets" / args.engine / "001_action_datasets.sql"
    print(f"DDL: {sql}")
    print(f"mode={'apply' if args.apply else 'dry-run'}")
    if not args.apply:
        print(sql.read_text())


if __name__ == "__main__":
    main()
