from pathlib import Path
import subprocess
import sys


TOOLS = Path(__file__).resolve().parents[1]


def test_dry_run_uses_uvicorn_module_with_requested_bind_address():
    result = subprocess.run(
        [sys.executable, "start_function_service.py", "--host", "0.0.0.0", "--port", "9876", "--dry-run"],
        cwd=TOOLS,
        check=True,
        capture_output=True,
        text=True,
    )
    assert f"-m uvicorn fn_service:app --app-dir {TOOLS} --host 0.0.0.0 --port 9876" in result.stdout
