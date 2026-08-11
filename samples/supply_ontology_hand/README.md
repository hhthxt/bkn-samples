# Supply Chain Ontology · Hand Experience Pack

[中文版 (Chinese)](./README_cn.md)

- **Sample slug:** `supply_ontology_hand`
- **KN ID:** `supply_ontology_hand`
- **Display name:** 供应链本体知识网络-手工版
- **Data:** 12 CSV files (anonymized, ~16MB)
- **Object types:** 11 bound + 1 skipped (`mon_task`, `bind:false`)

## Documentation

| Language | Import guide | Scenario design |
|----------|--------------|-----------------|
| English | [openbkn-hand-import-guide.md](docs/openbkn-hand-import-guide.md) | [agent-scenario-kn-capability-design.md](docs/agent-scenario-kn-capability-design.md) |
| 中文 | [openbkn-hand-import-guide_cn.md](docs/openbkn-hand-import-guide_cn.md) | [agent-scenario-kn-capability-design_cn.md](docs/agent-scenario-kn-capability-design_cn.md) |

## Quick start

1. Copy `tools/config.example.yaml` → `tools/config.yaml` and fill in database / OpenBKN settings
2. Follow [openbkn-hand-import-guide.md](docs/openbkn-hand-import-guide.md) steps 1–7 ([中文](docs/openbkn-hand-import-guide_cn.md))
3. Smoke test:

```bash
cd tools
python3 smoke_test.py --config config.yaml
```

## Tools

| Script | Step | Description |
|--------|------|-------------|
| `import_kn.py` | 2 | Import `kn/supply_ontology_hand.json` |
| `load_sample_data.py` | 3 | Load `data/*.csv` into your database |
| `setup_catalog.py` | 4 | Create / enable Catalog and discover tables |
| `bind_kn_resources.py` | 5 | Bind object types to Catalog resources |
| `smoke_test.py` | Verify | KN name, OT row counts, join hit rates |

## Package layout

```
supply_ontology_hand/
├── kn/supply_ontology_hand.json
├── data/
├── tools/
└── docs/          # EN + _cn guides (see table above)
```

## Dependencies

```bash
cd tools
pip install -r requirements.txt
```
