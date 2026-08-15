"""Runtime contract: function service consumes inline resolved_context only."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from context.contract import SOURCE_OFFLINE_TEST
from context.operation_contracts import OPERATION_CONTRACTS
from fn.snapshot import load_csv_snapshot
from fn_service import app
from service_dependencies import get_snapshot_source
from support_resolved_context import csv_resolved_context

SERVICE_PATH = Path(__file__).resolve().parents[1] / "fn_service.py"
DEPENDENCY_PATH = Path(__file__).resolve().parents[1] / "service_dependencies.py"


def _offline_client() -> TestClient:
    app.dependency_overrides[get_snapshot_source] = lambda: SOURCE_OFFLINE_TEST
    return TestClient(app)


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_fn_service_source_does_not_load_csv_at_import():
    text = SERVICE_PATH.read_text(encoding="utf-8")
    assert "SNAPSHOT = load_csv_snapshot()" not in text
    assert "load_csv_snapshot(" not in text


def test_fn_service_has_no_remote_client_imports():
    combined = SERVICE_PATH.read_text(encoding="utf-8") + "\n" + DEPENDENCY_PATH.read_text(
        encoding="utf-8"
    )
    forbidden = (
        "import mcp",
        "from mcp",
        "import httpx",
        "import requests",
        "import urllib",
        "import subprocess",
        "import socket",
        "openbkn",
        "ContextLoader",
        "ClientSession",
    )
    for token in forbidden:
        assert token not in combined


def test_runtime_requires_resolved_context():
    client = TestClient(app)
    response = client.post(
        "/functions/total-sellable",
        json={"product": "382-000005", "substitute_enabled": False},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "context_required"


def test_missing_dataset_returns_snapshot_incomplete():
    client = TestClient(app)
    response = client.post(
        "/functions/total-sellable",
        json={
            "product": "382-000005",
            "substitute_enabled": False,
            "resolved_context": csv_resolved_context(rows={"bom": []}),
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "snapshot_incomplete"


def test_missing_receipt_returns_receipt_required():
    client = TestClient(app)
    snap = load_csv_snapshot()
    response = client.post(
        "/functions/total-sellable",
        json={
            "product": "382-000005",
            "substitute_enabled": False,
            "resolved_context": csv_resolved_context(
                rows={"bom": snap.bom, "inventory": snap.inventory},
                bkn_receipts=[],
            ),
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "receipt_required"


def test_stale_context_returns_409():
    client = TestClient(app)
    snap = load_csv_snapshot()
    stale = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    response = client.post(
        "/functions/total-sellable",
        json={
            "product": "382-000005",
            "substitute_enabled": False,
            "resolved_context": csv_resolved_context(
                captured_at=stale,
                rows={"bom": snap.bom, "inventory": snap.inventory},
                bkn_receipts=[
                    {
                        "dataset": "bom",
                        "interaction_id": "int-test",
                    },
                    {
                        "dataset": "inventory",
                        "interaction_id": "int-test",
                    },
                ],
            ),
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"]["error"] == "context_stale"


def test_offline_test_mode_can_use_csv_rows_without_receipts():
    client = _offline_client()
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
    assert result["total_sellable_qty"] == 534
    assert result["snapshot_meta"]["source"] == "offline_test"
    assert result["snapshot_meta"]["input_digest"]
    assert result["snapshot_meta"]["snapshot_id"]


def test_runtime_never_auto_reads_csv(monkeypatch):
    def boom(*_args, **_kwargs):
        raise AssertionError("runtime must not read CSV")

    monkeypatch.setattr("fn.snapshot.load_csv_snapshot", boom)
    monkeypatch.setattr("fn_service.load_csv_snapshot", boom, raising=False)
    client = TestClient(app)
    response = client.post(
        "/functions/total-sellable",
        json={"product": "382-000005", "substitute_enabled": False},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "context_required"


def test_health_and_ready_are_not_tools():
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"
    ready = client.get("/ready").json()
    assert ready["status"] == "ok"
    assert ready["snapshot_source"] == "openbkn"
    assert "open_forecast_count" in ready["operations"] or "bom_list" in ready["operations"]
    spec = client.get("/openapi.json").json()
    assert "/health" not in spec["paths"]
    assert "/ready" not in spec["paths"]


def test_ready_only_reports_registered_business_routes():
    client = TestClient(app)
    registered = sorted(
        operation["operationId"]
        for methods in client.get("/openapi.json").json()["paths"].values()
        for operation in methods.values()
    )
    operations = client.get("/ready").json()["operations"]

    assert operations == registered
    not_yet_routed = set(OPERATION_CONTRACTS) - set(registered)
    assert set(operations).isdisjoint(not_yet_routed)
