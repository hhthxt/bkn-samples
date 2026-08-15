from pathlib import Path
import yaml
from sqlalchemy import create_engine, text
from load_sample_data import load_all

PACK = Path(__file__).resolve().parents[2]
SAMPLE = PACK / "data"
MAP = PACK / "tools" / "mapping" / "object_table_map.yaml"

def test_load_three_tables_sqlite(tmp_path):
    mapping = yaml.safe_load(MAP.read_text(encoding="utf-8"))
    mapping["load_order"] = ["erp_material", "hd_product_view", "customer_entity"]
    engine = create_engine(f"sqlite:///{tmp_path/'t.db'}")
    cfg = {
        "database": {"engine": "sqlite"},
        "load": {"sample_dir": str(SAMPLE), "mode": "recreate", "on_error": "stop"},
    }
    report = load_all(engine, cfg, mapping)
    assert report["erp_material"] > 0
    assert report["hd_product_view"] > 0
    with engine.connect() as conn:
        n = conn.execute(text("select count(*) from hd_product_view")).scalar()
        assert n == report["hd_product_view"]
