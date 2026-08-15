"""Safe open-forecast-count Tool: always exclude closed forecasts."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from context.contract import SOURCE_OFFLINE_TEST
from fn.forecast import open_forecast_count
from fn_service import app
from service_dependencies import get_snapshot_source
from support_resolved_context import csv_resolved_context, forecast_rows_from_csv


CLOSED = "Closed"
SAMPLE_ROWS = [
    {"id": "f-open-a", "material_number": "382-000005", "closestatus_title": "Normal"},
    {"id": "f-closed-a", "material_number": "382-000005", "closestatus_title": "Closed"},
    {"id": "f-open-b", "material_number": "U00-000151", "closestatus_title": "Normal"},
    {"id": "f-blank", "material_number": "U00-000151", "closestatus_title": ""},
]


def _independent_open_count(rows: list[dict], product_code: str | None = None) -> int:
    count = 0
    for row in rows:
        if (row.get("closestatus_title") or "").strip() == CLOSED:
            continue
        if product_code and (row.get("material_number") or "").strip() != product_code:
            continue
        count += 1
    return count


def _offline_client() -> TestClient:
    app.dependency_overrides[get_snapshot_source] = lambda: SOURCE_OFFLINE_TEST
    return TestClient(app)


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_open_forecast_count_excludes_closed_rows():
    result = open_forecast_count(SAMPLE_ROWS)
    assert result["open_count"] == 3
    assert result["excluded_closed_count"] == 1
    assert result["input_row_count"] == 4
    assert result["exclusion"] == {
        "field": "closestatus_title",
        "operation": "!=",
        "value": CLOSED,
    }
    assert "f-closed-a" not in result["open_forecast_ids"]
    assert result["open_forecast_ids"] == ["f-open-a", "f-open-b", "f-blank"]


def test_open_forecast_count_filters_optional_product_code():
    result = open_forecast_count(SAMPLE_ROWS, product_code="382-000005")
    assert result["open_count"] == 1
    assert result["product_code"] == "382-000005"
    assert result["open_forecast_ids"] == ["f-open-a"]


def test_open_forecast_count_matches_independent_csv_count():
    rows = forecast_rows_from_csv()
    result = open_forecast_count(rows)
    assert result["open_count"] == _independent_open_count(rows)
    assert result["excluded_closed_count"] == sum(
        1 for row in rows if (row.get("closestatus_title") or "").strip() == CLOSED
    )
    filtered = open_forecast_count(rows, product_code="382-000005")
    assert filtered["open_count"] == _independent_open_count(rows, "382-000005")


def test_openapi_has_no_include_closed_parameter():
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    operation = spec["paths"]["/functions/open-forecast-count"]["post"]
    schema = spec["components"]["schemas"]["OpenForecastCountRequest"]
    assert "include_closed" not in schema.get("properties", {})
    assert set(schema.get("properties", {})) <= {
        "resolved_context",
        "product_code",
    }
    assert operation["operationId"] == "open_forecast_count"
    assert operation["summary"] == "未关闭预测单数"


def test_open_forecast_count_endpoint_returns_snapshot_meta():
    client = _offline_client()
    rows = forecast_rows_from_csv()
    response = client.post(
        "/functions/open-forecast-count",
        json={"resolved_context": csv_resolved_context()},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["open_count"] == _independent_open_count(rows)
    assert body["snapshot_meta"]["source"] == "offline_test"
    assert body["snapshot_meta"]["input_digest"]
    assert "forecast" in body["snapshot_meta"]["loaded_datasets"]


def test_open_forecast_count_rejects_missing_forecast_rows():
    client = TestClient(app)
    response = client.post(
        "/functions/open-forecast-count",
        json={
            "resolved_context": {
                "knowledge_network_id": "supply_ontology_hand",
                "conversation_id": "conv-test",
                "interaction_id": "int-test",
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "bkn_receipts": [],
                "rows": {"bom": []},
            }
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "snapshot_incomplete"


def test_open_forecast_count_requires_receipt_in_openbkn_mode():
    client = TestClient(app)
    response = client.post(
        "/functions/open-forecast-count",
        json={
            "resolved_context": csv_resolved_context(
                rows={"forecast": SAMPLE_ROWS},
                bkn_receipts=[],
            )
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "receipt_required"
