"""HTTP/OpenAPI contract tests for the supply-chain function toolbox."""

import re

import pytest
from fastapi.testclient import TestClient

from context.contract import SOURCE_OFFLINE_TEST
from export_fn_openapi import build_toolbox_openapi
from fn_service import app
from service_dependencies import get_snapshot_source
from support_resolved_context import csv_resolved_context


@pytest.fixture
def client():
    app.dependency_overrides[get_snapshot_source] = lambda: SOURCE_OFFLINE_TEST
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_openapi_exposes_all_business_functions(client):
    spec = client.get("/openapi.json").json()
    operation_ids = {
        operation["operationId"]
        for methods in spec["paths"].values()
        for operation in methods.values()
    }
    assert operation_ids == {
        "bom_list",
        "bom_shared_list",
        "layered_inventory",
        "substitute_status",
        "theoretical_build",
        "total_sellable",
        "kitting_net_demand",
        "shared_contention",
        "max_build_without_po",
        "leadtime_days",
        "supply_status",
        "open_forecast_count",
        "backward_plan",
    }


def test_total_sellable_endpoint_matches_csv_gold(client):
    response = client.post(
        "/functions/total-sellable",
        json={
            "product": "382-000005",
            "substitute_enabled": False,
            "resolved_context": csv_resolved_context(),
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result["fg_qty"] == 534
    assert result["theoretical_build_qty"] == 0
    assert result["total_sellable_qty"] == 534
    assert result["include_in_transit"] is False


def test_bom_shared_endpoint_supports_three_products(client):
    response = client.post(
        "/functions/bom-shared-list",
        json={
            "products": ["382-000005", "P61-000351", "U00-000151"],
            "include_substitute": False,
            "resolved_context": csv_resolved_context(),
        },
    )
    assert response.status_code == 200
    assert response.json()["shared_count"] == 11


def test_business_precondition_returns_structured_422(client):
    response = client.post(
        "/functions/bom-shared-list",
        json={
            "products": ["382-000005"],
            "resolved_context": csv_resolved_context(),
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "cannot_compute"


def test_health_endpoint_is_not_registered_as_tool(client):
    assert client.get("/health").json() == {
        "status": "ok",
        "knowledge_network_id": "supply_ontology_hand",
    }
    spec = client.get("/openapi.json").json()
    assert "/health" not in spec["paths"]


def test_exported_openapi_is_toolbox_compatible():
    spec = build_toolbox_openapi()
    encoded = str(spec)
    assert spec["openapi"] == "3.0.3"
    assert spec["servers"] == [{"url": "http://host.docker.internal:8765"}]
    assert "'type': 'null'" not in encoded
    for methods in spec["paths"].values():
        for operation in methods.values():
            assert re.fullmatch(r"[\u4e00-\u9fffA-Za-z0-9_]+", operation["summary"])
