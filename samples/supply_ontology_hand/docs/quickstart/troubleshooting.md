# 常见问题

## `ModuleNotFoundError`

推荐先进入 `tools/`：

```bash
cd .../supply_ontology_hand/tools
python3 -m pytest tests -q
```

如果从包根运行，使用 `PYTHONPATH=tools`。

## `forecast_id` 不存在

离线样例使用 `erp_mds_forecast.csv` 中的 ID。可先查找未关闭预测：

```bash
python3 - <<'PY'
import csv
with open('data/erp_mds_forecast.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row['closestatus_title'] != '已关闭':
            print(row['id'], row['material_number'], row['qty'], row['enddate'])
            break
PY
```

## 在线调用返回 `receipt_required`

每个非空远程数据集都必须有归属于当前 `interaction_id` 的官方查询回执。不要用手工构造的 receipt 代替官方回执。

## 结果无法计算

先区分数据不足、替代料未确认、没有截止日、预测单不存在和上下文过期。不要把缺失数据解释成“可交付”或“无需采购”。

## Action 没有写入 ERP

这是设计边界。Action 只记录采购决策和生产监控建议；必须有人批准，且默认 dry-run。
