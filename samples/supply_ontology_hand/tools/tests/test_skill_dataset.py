from pathlib import Path

import pytest

from setup_skill_dataset import expected_tables, load_skill_entries, prompt_database_name, seed_rows


def test_skill_registry_has_idempotent_table_and_required_columns():
    assert expected_tables() == {"skills"}
    sql = (Path(__file__).parents[2] / "datasets" / "postgres" / "002_skill_registry.sql").read_text()
    for column in ("skill_id", "name", "description", "status", "kn_id", "object_type_ids", "skill_query"):
        assert column in sql


def test_seed_rows_are_dataset_records_for_published_skills():
    rows = seed_rows([
        {"id": "skill-1", "name": "demo", "description": "demo desc", "status": "published"}
    ], kn_id="supply_ontology_hand")
    assert rows == [{
        "skill_id": "skill-1",
        "name": "demo",
        "description": "demo desc",
        "version": "",
        "status": "published",
        "business_domain_id": "",
        "kn_id": "supply_ontology_hand",
        "object_type_ids": ["skills"],
        "skill_query": "demo demo desc",
    }]


def test_database_name_must_be_explicit_for_isolated_deployment(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "")
    with pytest.raises(ValueError, match="数据库名不能为空"):
        prompt_database_name()


def test_load_skill_entries_accepts_cli_data_and_keeps_published_only():
    payload = {"total": 2, "data": [
        {"skill_id": "s1", "name": "one", "description": "d", "status": "published"},
        {"skill_id": "s2", "name": "two", "description": "d", "status": "unpublish"},
    ]}
    assert load_skill_entries(payload) == [payload["data"][0]]
