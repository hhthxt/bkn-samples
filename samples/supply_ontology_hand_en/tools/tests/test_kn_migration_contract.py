import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]


def load_kn(sample_name, filename):
    return json.loads(
        (REPO_ROOT / "samples" / sample_name / "kn" / filename).read_text()
    )


def test_chinese_kn_is_full_capability_snapshot():
    kn = load_kn("supply_ontology_hand", "supply_ontology_hand.json")
    object_ids = {item["id"] for item in kn["object_types"]}
    action_ids = {item["id"] for item in kn["action_types"]}

    assert len(object_ids) >= 14
    assert len(kn["relation_types"]) >= 13
    assert "skills" in object_ids
    assert "supply_ontology_hand_act_mon_close" in action_ids


def test_kn_has_no_environment_specific_resource_ids():
    for sample_name, filename in (
        ("supply_ontology_hand", "supply_ontology_hand.json"),
        ("supply_ontology_hand_en", "supply_ontology_hand_en.json"),
    ):
        text = (
            REPO_ROOT / "samples" / sample_name / "kn" / filename
        ).read_text()
        assert "d9v" not in text
        assert "localhost" not in text.lower()


def test_english_kn_preserves_technical_ids():
    zh = load_kn("supply_ontology_hand", "supply_ontology_hand.json")
    en = load_kn("supply_ontology_hand_en", "supply_ontology_hand_en.json")
    assert {item["id"] for item in zh["object_types"]} == {
        item["id"] for item in en["object_types"]
    }
    assert {item["id"] for item in zh["relation_types"]} == {
        item["id"] for item in en["relation_types"]
    }
    assert {item["id"] for item in zh["action_types"]} == {
        item["id"] for item in en["action_types"]
    }


def test_english_kn_has_no_chinese_display_text():
    text = (REPO_ROOT / "samples/supply_ontology_hand_en/kn/supply_ontology_hand_en.json").read_text()
    assert not re.search(r"[\u3400-\u4dbf\u4e00-\u9fff]", text)
