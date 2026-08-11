"""Tests for import_kn step-2 script."""

from __future__ import annotations

import json
from pathlib import Path

from import_kn import import_kn

KN = Path(__file__).resolve().parents[2] / "kn" / "supply_ontology_hand.json"


def test_import_kn_dry_run():
    report = import_kn(KN, dry_run=True)
    assert report["kn_id"] == "supply_ontology_hand"
    assert report["kn_name"] == "供应链本体知识网络-手工版"
    assert report["action"] == "would_import"


def test_kn_json_has_required_fields():
    payload = json.loads(KN.read_text(encoding="utf-8"))
    assert payload["id"] == "supply_ontology_hand"
    assert len(payload["id"]) <= 32
    assert isinstance(payload.get("object_types"), list)
    assert len(payload["object_types"]) > 0
