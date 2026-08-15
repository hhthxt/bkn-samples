from __future__ import annotations


def test_existing_native_tool_is_updated_with_current_function_bundle(monkeypatch):
    import register_native_function_toolbox as registry

    calls: list[list[str]] = []

    def fake_call(args):
        calls.append(args)
        if args[:2] == ["toolbox", "list"]:
            return {"data": [{"box_name": "供应链原生计算函数", "box_id": "box-1", "status": "published"}]}
        if args[:2] == ["tool", "list"]:
            return {"tools": [{"name": registry.TOOL_NAME, "tool_id": "tool-1", "status": "enabled"}]}
        return {}

    monkeypatch.setattr(registry, "_call", fake_call)

    result = registry.run(box_name="供应链原生计算函数", apply=True)

    assert result["box_id"] == "box-1"
    assert result["tool_id"] == "tool-1"
    update = next(call for call in calls if call[:3] == ["call", "/api/agent-operator-integration/v1/tool-box/box-1/tool/tool-1", "-X"])
    assert update[3] == "POST"
    assert '"metadata_type": "function"' in update[5]
    assert '"name": "supply_chain_compute"' in update[5]
    assert ["toolbox", "publish", "box-1"] not in calls
