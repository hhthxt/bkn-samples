from __future__ import annotations

from support_resolved_context import csv_resolved_context


def test_native_function_bundle_runs_total_sellable_without_external_service():
    from native_function_bundle import build_native_function_code

    namespace: dict[str, object] = {}
    exec(build_native_function_code(), namespace)

    context = csv_resolved_context(
        bkn_receipts=[
            {"dataset": "bom", "interaction_id": "int-test"},
            {"dataset": "inventory", "interaction_id": "int-test"},
        ]
    )
    result = namespace["handler"](
        {
            "operation": "total_sellable",
            "parameters": {
                "product": "382-000005",
                "substitute_enabled": False,
                "resolved_context": context,
            },
        }
    )

    assert result["total_sellable_qty"] == 534
    assert result["snapshot_meta"]["source"] == "openbkn"


def test_native_function_bundle_is_self_contained_and_uses_handler_entrypoint():
    from native_function_bundle import build_native_function_code

    code = build_native_function_code()
    assert "def handler(event):" in code
    assert "host.docker.internal" not in code
    assert "http://" not in code
