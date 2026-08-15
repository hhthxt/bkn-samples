from bind_skill_dataset import build_binding


def test_build_binding_uses_resource_source():
    assert build_binding("supply_ontology_hand", "skills", "resource-1") == {
        "kn_id": "supply_ontology_hand",
        "object_type_id": "skills",
        "data_source": {"type": "resource", "id": "resource-1"},
    }
