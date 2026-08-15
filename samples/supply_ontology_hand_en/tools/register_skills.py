"""Describe dataset-backed Skill registration without embedding environment IDs."""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    print(f"skill_directory={root / 'skills'}")
    print("object_type=skills")
    print("dataset=public.skills (create with setup_skill_dataset.py, then Discover and bind with bind_skill_dataset.py)")
    print(f"mode={'apply' if args.apply else 'dry-run'}")


if __name__ == "__main__":
    main()
