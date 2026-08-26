from __future__ import annotations

import pytest

from toolbox_resolution import ToolboxResolutionError, resolve_published_toolbox


def test_resolves_current_published_box_by_name_and_enabled_tools():
    result = resolve_published_toolbox(
        {
            "data": [
                {"box_name": "供应链计算函数工具箱", "box_id": "old", "status": "draft"},
                {
                    "box_name": "供应链计算函数工具箱",
                    "box_id": "current",
                    "status": "published",
                    "version": "2",
                    "updated_at": "2026-08-26T10:00:00Z",
                },
            ]
        },
        {"tools": [{"name": f"fn_{i}", "status": "enabled"} for i in range(13)]},
        name="供应链计算函数工具箱",
        required_tool_count=13,
    )

    assert result["box_id"] == "current"
    assert result["box_name"] == "供应链计算函数工具箱"
    assert result["status"] == "published"
    assert result["enabled_tool_count"] == 13


def test_rejects_published_box_with_disabled_tool():
    with pytest.raises(ToolboxResolutionError, match="enabled"):
        resolve_published_toolbox(
            {"data": [{"box_name": "供应链计算函数工具箱", "box_id": "box", "status": "published"}]},
            {"tools": [{"name": "fn", "status": "disabled"}]},
            name="供应链计算函数工具箱",
            required_tool_count=1,
        )


def test_rejects_missing_exact_name_instead_of_falling_back_to_old_id():
    with pytest.raises(ToolboxResolutionError, match="published toolbox"):
        resolve_published_toolbox(
            {"data": [{"box_name": "供应链原生计算函数", "box_id": "other", "status": "published"}]},
            {"tools": []},
            name="供应链计算函数工具箱",
        )
