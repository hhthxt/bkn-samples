# Supply Chain Ontology · Hand Experience Pack

[中文版 (Chinese)](./README_cn.md)

- **Sample slug:** `supply_ontology_hand`
- **KN ID:** `supply_ontology_hand`
- **Display name:** 供应链本体知识网络-手工版
- **Data:** 12 CSV files (anonymized, ~16MB)
- **Object types:** 11 bound + 1 skipped (`mon_task`, `bind:false`)

## Documentation

[供应链本体 Handbook HTML](./docs/handbook.html) · [Agent 操作](./docs/agent-operation-guide.md) · [手工操作](./docs/manual-operation-guide.md) · [线上数据推送](./docs/online-data-push.md) · [第三方 FAQ](./docs/faq.md) · [POC 验证报告](./docs/verification/poc-verification-report-2026-08-15.md) · [Playbook](./docs/playbook.md) · [QA 测试集](./docs/qa-eval-set.yaml)

Canonical design is **Chinese** (this sample’s KN model and CSVs are Chinese):

| Doc | Purpose |
|-----|---------|
| [Import guide](docs/openbkn-hand-import-guide.md) · [中文](docs/openbkn-hand-import-guide_cn.md) | Steps 1–7: import KN → load CSV → catalog → bind |
| [场景驱动的供应链动态能力设计](docs/场景驱动的供应链动态能力设计.md) | **Main design** for this KN + sample data |
| [能力口径清单](docs/能力口径清单.md) | Metric / function / skill / action caliber |
| [业务问答测试集](docs/业务问答测试集.md) | 5–10 business Q&As per capability + CSV snapshots |
| [Agent 导入验证清单](docs/Agent导入验证清单.md) | Post-import verification |
| [动力层落地方案](docs/动力层建设方案.md) | Metrics / functions / skills / actions after bind |
| [动力层落地说明书](docs/动力层落地说明书.md) | Step 8: metrics + function lib/CLI + skill register |
| [metrics-create.json](docs/payloads/metrics-create.json) | Metric create payload |
| [metrics-query-examples.json](docs/payloads/metrics-query-examples.json) | Runnable query bodies + expected snapshots |
| [logic-properties.json](docs/payloads/logic-properties.json) | Metric → object logic-property bindings |
| [Business story Playbook](docs/playbook/fulfillment-commitment-playbook.md) | End-to-end fulfillment commitment story |
| [Agent conversation Playbook](docs/playbook/agent-conversation.md) | Human-Agent turns and Action confirmation |
| [Offline quickstart](docs/quickstart/offline.md) | Run without OpenBKN credentials |
| [OpenBKN online path](docs/quickstart/online-openbkn.md) | Third-party Context Loader handoff |
| [Metrics](docs/catalog/metrics.md) · [Functions](docs/catalog/functions.md) · [Actions](docs/catalog/actions.md) | Local capability catalog |
| [Capability registry](docs/power-layer/capability-registry.yaml) | Entry points and verification mapping |

## Quick start

### Recommended: run the offline story first

```bash
cd tools
python3 run_scenario.py --scenario fulfillment-commitment \
  --product U00-000080 --forecast-id 0000023181-FUTURE \
  --demand-end 2026-10-31 --demand-qty 3000 \
  --output /tmp/fulfillment-report.json
```

This runs S1 backward planning, S2 sellable capacity, and produces controlled Action proposals. See the [offline quickstart](docs/quickstart/offline.md).

### Then connect OpenBKN

1. Copy `tools/config.example.yaml` → `tools/config.yaml` and fill in database / OpenBKN settings
2. Follow [openbkn-hand-import-guide.md](docs/openbkn-hand-import-guide.md) steps 1–7 ([中文](docs/openbkn-hand-import-guide_cn.md))
3. Smoke test, then power layer (step 8):

```bash
cd tools
python3 smoke_test.py --config config.yaml
python3 power_layer.py all --kn-id supply_ontology_hand
```

## Tools

| Script | Step | Description |
|--------|------|-------------|
| `import_kn.py` | 2 | Import `kn/supply_ontology_hand.json` |
| `load_sample_data.py` | 3 | Load `data/*.csv` into your database |
| `setup_catalog.py` | 4 | Create / enable Catalog and discover tables |
| `bind_kn_resources.py` | 5 | Bind object types to Catalog resources |
| `smoke_test.py` | Verify | KN name, OT row counts, join hit rates |
| `power_layer.py` | 8 | Create metrics, bind logic properties, verify snapshots |
| `fn/` · `fn_cli.py` | 8 | CSV-gold function library and offline CLI |
| `fn_service.py` · `export_fn_openapi.py` | 8 | Toolbox HTTP service and OpenAPI export |
| `metrics.py` | Local | Eight P0 metrics over sample CSVs |
| `scenario/` · `run_scenario.py` | Local | Offline business-story runner |
| `actions/` | Local | Approval, decision, monitoring and dry-run Actions |
| `eval/cases/` | Verify | Independent golden cases and 95%+ evaluation |

## Package layout

```
supply_ontology_hand/
├── kn/supply_ontology_hand.json
├── data/
├── tools/         # power_layer + fn/ + CLI + OpenAPI service
├── skills/        # S1 / S2 / S3
└── docs/
```

## Localization (current status)

This is the Chinese, one-shot delivery sample. It includes the complete verified capability set: ontology, data binding, metrics, Skills, functions, Actions, Playbook, Agent mode, and manual mode.

Use the future forecast cases in `docs/qa-eval-set.yaml` for benchmark validation. Forecast `0000023181` is retained only as a historical regression case.

The independent English sample is available at `../supply_ontology_hand_en/`.

## Dependencies

```bash
cd tools
pip install -r requirements.txt
```
