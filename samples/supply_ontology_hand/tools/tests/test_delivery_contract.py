from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]


REQUIRED_FILES = (
    "README.md",
    "kn/{kn_file}",
    "data/erp_mds_forecast.csv",
    "docs/agent-operation-guide.md",
    "docs/manual-operation-guide.md",
    "docs/playbook.md",
    "docs/qa-eval-set.yaml",
    "docs/handbook.html",
    "docs/sample-contract.yaml",
    "tools/import_kn.py",
    "tools/bind_kn_resources.py",
    "tools/load_sample_data.py",
)


def test_chinese_sample_is_self_contained():
    sample = REPO_ROOT / "samples" / "supply_ontology_hand"
    missing = [
        path.format(kn_file="supply_ontology_hand.json")
        for path in REQUIRED_FILES
        if not (sample / path.format(kn_file="supply_ontology_hand.json")).is_file()
    ]
    assert not missing, f"Chinese sample missing delivery files: {missing}"


def test_english_sample_is_self_contained():
    sample = REPO_ROOT / "samples" / "supply_ontology_hand_en"
    missing = [
        path.format(kn_file="supply_ontology_hand_en.json")
        for path in REQUIRED_FILES
        if not (sample / path.format(kn_file="supply_ontology_hand_en.json")).is_file()
    ]
    assert not missing, f"English sample missing delivery files: {missing}"


def test_samples_do_not_use_stage_directories():
    for sample_name in ("supply_ontology_hand", "supply_ontology_hand_en"):
        sample = REPO_ROOT / "samples" / sample_name
        assert not any(path.is_dir() for path in sample.glob("stage*"))
