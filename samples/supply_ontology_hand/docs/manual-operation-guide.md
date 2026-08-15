# 手工操作手册

## 一次性流程

```bash
cd tools
python3 load_sample_data.py --config config.yaml
python3 import_kn.py --kn-file ../kn/supply_ontology_hand.json
python3 bind_kn_resources.py --config config.yaml --kn-id supply_ontology_hand
python3 verify_sample.py --config config.yaml --kn-id supply_ontology_hand
```

再按 `tools/setup_action_datasets.py`、Skill 注册和函数服务说明完成动力层配置。所有写入命令先使用 `--dry-run`，确认资源和影响范围后再执行。

## 供应承诺问题

使用 `docs/qa-eval-set.yaml` 中的未来预测案例，记录查询结果、计算证据和最终结论。
