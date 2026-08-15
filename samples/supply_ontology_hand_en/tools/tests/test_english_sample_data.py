import csv
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


def test_english_sample_data_has_no_cjk_business_text():
    data_dir = REPO_ROOT / "samples" / "supply_ontology_hand_en" / "data"
    for path in sorted(data_dir.glob("*.csv")):
        with path.open(newline="") as handle:
            for row_number, row in enumerate(csv.reader(handle), start=1):
                assert not any(CJK.search(value) for value in row), (
                    f"Chinese text remains in {path.name}:{row_number}"
                )


def test_english_and_chinese_data_have_same_file_shapes():
    zh_dir = REPO_ROOT / "samples" / "supply_ontology_hand" / "data"
    en_dir = REPO_ROOT / "samples" / "supply_ontology_hand_en" / "data"
    assert {p.name for p in zh_dir.glob("*.csv")} == {
        p.name for p in en_dir.glob("*.csv")
    }
    for path in sorted(zh_dir.glob("*.csv")):
        with path.open(newline="") as zh_handle, (en_dir / path.name).open(
            newline=""
        ) as en_handle:
            assert len(list(csv.reader(zh_handle))) == len(list(csv.reader(en_handle)))
