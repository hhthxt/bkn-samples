from __future__ import annotations
import importlib.util
from pathlib import Path

path = Path(__file__).resolve().parents[2] / "eval" / "evaluate.py"
spec = importlib.util.spec_from_file_location("sample_eval_root", path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
load_cases = module.load_cases
evaluate_local_sample = module.evaluate_local_sample
