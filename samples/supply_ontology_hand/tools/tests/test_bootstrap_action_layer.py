from pathlib import Path

from bootstrap_action_layer import resolve_path


def test_resolve_path_accepts_sample_root_relative_tools_path():
    root = Path("/sample/tools")
    assert resolve_path(root, "tools/config.poc.yaml") == Path("/sample/tools/config.poc.yaml")
