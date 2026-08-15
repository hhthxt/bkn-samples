from __future__ import annotations

import base64
import json
import zlib

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


def test_native_function_bundle_normalizes_bom_usage_from_numerator_and_denominator():
    from native_function_bundle import build_native_function_code

    namespace: dict[str, object] = {}
    exec(build_native_function_code(), namespace)

    context = csv_resolved_context(
        rows={
            "bom": [
                {
                    "bom_material_code": "P-1",
                    "parent_material_code": "P-1",
                    "material_code": "C-1",
                    "bom_level": 1,
                    "usage_numerator": "2",
                    "usage_denominator": "1",
                    "alt_priority": 0,
                }
            ]
        },
        bkn_receipts=[{"dataset": "bom", "interaction_id": "int-test"}],
    )

    result = namespace["handler"](
        {
            "operation": "bom_list",
            "parameters": {
                "product": "P-1",
                "resolved_context": context,
            },
        }
    )

    assert result["lines"][0]["standard_usage"] == 2.0


def test_native_function_bundle_accepts_compressed_resolved_context():
    from native_function_bundle import build_native_function_code

    namespace: dict[str, object] = {}
    exec(build_native_function_code(), namespace)
    context = csv_resolved_context(
        bkn_receipts=[
            {"dataset": "bom", "interaction_id": "int-test"},
            {"dataset": "inventory", "interaction_id": "int-test"},
        ]
    )
    packed = base64.b64encode(zlib.compress(json.dumps(context).encode("utf-8"))).decode("ascii")

    result = namespace["handler"](
        {
            "operation": "total_sellable",
            "parameters": {
                "product": "382-000005",
                "substitute_enabled": False,
                "resolved_context_compressed": packed,
            },
        }
    )

    assert result["total_sellable_qty"] == 534


def test_native_function_bundle_uses_compressed_context_for_open_forecast_count():
    from native_function_bundle import build_native_function_code

    namespace: dict[str, object] = {}
    exec(build_native_function_code(), namespace)
    context = csv_resolved_context(
        rows={
            "forecast": [
                {"id": "F-1", "material_number": "P-1", "closestatus_title": "正常"},
                {"id": "F-2", "material_number": "P-1", "closestatus_title": "已关闭"},
            ]
        },
        bkn_receipts=[{"dataset": "forecast", "interaction_id": "int-test"}],
    )
    packed = base64.b64encode(zlib.compress(json.dumps(context).encode("utf-8"))).decode("ascii")

    result = namespace["handler"](
        {
            "operation": "open_forecast_count",
            "parameters": {
                "product_code": "P-1",
                "resolved_context_compressed": packed,
            },
        }
    )

    assert result["open_count"] == 1
