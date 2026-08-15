"""HTTP contract for the backward_plan toolbox tool."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from context.contract import SOURCE_OFFLINE_TEST
from export_fn_openapi import build_toolbox_openapi
from fn_service import app
from service_dependencies import get_snapshot_source
from test_backward_plan import DEMAND_END, FORECAST_ID, PRODUCT, rows


def _context(**row_overrides) -> dict:
    payload = rows(**row_overrides)
    return {
        "knowledge_network_id": "supply_ontology_hand",
        "conversation_id": "conv-test",
        "interaction_id": "int-test",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "bkn_receipts": [],
        "rows": payload,
    }


def _body(**overrides) -> dict:
    payload = {
        "product": PRODUCT,
        "forecast_id": FORECAST_ID,
        "demand_end": DEMAND_END,
        "demand_qty": 10,
        "substitute_enabled": False,
        "report_grain": "summary",
        "resolved_context": _context(),
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def client():
    app.dependency_overrides[get_snapshot_source] = lambda: SOURCE_OFFLINE_TEST
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_openapi_registers_backward_plan_as_thirteenth_tool(client):
    spec = client.get("/openapi.json").json()
    operation = spec["paths"]["/functions/backward-plan"]["post"]
    assert operation["operationId"] == "backward_plan"
    assert operation["summary"] == "生产计划齐套倒排"
    schema = spec["components"]["schemas"]["BackwardPlanRequest"]
    required = set(schema.get("required") or [])
    assert {
        "product",
        "forecast_id",
        "demand_end",
        "demand_qty",
        "substitute_enabled",
        "resolved_context",
    } <= required
    assert "today" not in schema.get("properties", {})
    ids = {
        op["operationId"]
        for methods in spec["paths"].values()
        for op in methods.values()
        if "operationId" in op
    }
    assert len(ids) == 13
    assert "backward_plan" in ids


def test_exported_openapi_has_thirteen_business_tools():
    spec = build_toolbox_openapi()
    ids = {
        op["operationId"]
        for methods in spec["paths"].values()
        for op in methods.values()
        if "operationId" in op
    }
    assert len(ids) == 13
    assert "backward_plan" in ids


def test_backward_plan_endpoint_returns_snapshot_meta(client):
    response = client.post("/functions/backward-plan", json=_body())
    assert response.status_code == 200
    body = response.json()
    assert body["product_code"] == PRODUCT
    assert body["forecast_id"] == FORECAST_ID
    assert body["snapshot_meta"]["source"] == "offline_test"
    assert body["snapshot_meta"]["input_digest"]
    assert "forecast" in body["snapshot_meta"]["loaded_datasets"]


def test_backward_plan_summary_and_full_tree(client):
    summary = client.post(
        "/functions/backward-plan", json=_body(report_grain="summary")
    ).json()
    full = client.post(
        "/functions/backward-plan", json=_body(report_grain="full_tree")
    ).json()
    assert summary["node_count_total"] == full["node_count_total"]
    assert len(full["nodes"]) == full["node_count_total"]
    assert len(summary["nodes"]) <= len(full["nodes"])


def test_backward_plan_rejects_empty_bom(client):
    response = client.post(
        "/functions/backward-plan",
        json=_body(resolved_context=_context(bom=[])),
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "cannot_compute"


def test_backward_plan_requires_resolved_context(client):
    payload = _body()
    payload.pop("resolved_context")
    response = client.post("/functions/backward-plan", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "context_required"


def test_backward_plan_requires_receipt_in_openbkn_mode():
    client = TestClient(app)
    response = client.post(
        "/functions/backward-plan",
        json=_body(),
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "receipt_required"


def test_backward_plan_rejects_incomplete_rows(client):
    context = _context()
    context["rows"].pop("mrp")
    response = client.post(
        "/functions/backward-plan",
        json=_body(resolved_context=context),
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "snapshot_incomplete"
