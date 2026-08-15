from bind_skill_dataset import build_binding, ensure_skill_registry_properties


def test_build_binding_uses_resource_source():
    assert build_binding("supply_ontology_hand", "skills", "resource-1") == {
        "kn_id": "supply_ontology_hand",
        "object_type_id": "skills",
        "data_source": {"type": "resource", "id": "resource-1"},
    }


def test_binding_payload_exposes_registry_scope_columns():
    body = {"data_properties": [{"name": "skill_id"}]}
    ensure_skill_registry_properties(body)
    assert {item["name"] for item in body["data_properties"]} >= {
        "skill_id", "version", "business_domain_id", "kn_id", "object_type_ids", "skill_query"
    }
    assert all(item.get("mapped_field", {}).get("name") == item["name"] for item in body["data_properties"])
