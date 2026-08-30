from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[2]


def test_capability_registry_declares_all_direct_functions_and_mcp_entrypoint():
    text = (PACKAGE / "docs" / "power-layer" / "capability-registry.yaml").read_text(encoding="utf-8")

    assert "version: 2" in text
    assert "供应链原生计算函数" in text
    assert "execute_published_tool" in text
    assert "material_where_used" in text
    assert "resolved_context" not in text


def test_agent_import_checklist_has_native_function_release_gate():
    text = (PACKAGE / "docs" / "Agent导入验证清单.md").read_text(encoding="utf-8")

    assert "register_native_function_toolbox.py --apply" in text
    assert "**14** 个 enabled" in text
    assert "execute_published_tool" in text
    assert "material_code=606-000989" in text
    assert "product=382-000005" in text
    assert "15 个 OT" not in text
