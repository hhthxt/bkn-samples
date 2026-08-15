"""Launch the local function service after configuration is supplied."""

import argparse
import os
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.getenv("SUPPLY_FN_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("SUPPLY_FN_PORT", "8765")))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    command = [sys.executable, "fn_service.py", "--host", args.host, "--port", str(args.port)]
    print(" ".join(command))
    if not args.dry_run:
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
