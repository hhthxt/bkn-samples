# S1 调用的 Metric / 函数

体验网：`supply_ontology_hand`。口径 SSOT：`docs/能力口径清单.md`。

本 Skill **不得**用 Metric 替代 BOM 倒排。仓口径用 `warehouse_scope`，不要把仓名单写死在公式里。

## Metric

| 名称 | 用法 |
|------|------|
| 库存可用量 | 按物料 + `warehouse_scope`（缺省生产 7 仓） |
| 预测需求量合计 | 可选对照；**不是**齐套结论 |

## 函数

| 函数 | 用途 | 离线 CLI |
|------|------|----------|
| BOM 清单 | 倒排前结构；无 BOM 终止 | `fn_cli.py bom-list` |
| 子料分层库存 | 各层可用（占用只展示） | `fn_cli.py layered` |
| 要 X 套净需求 | 缺料；在途=未关闭 PO 未清 | `fn_cli.py kitting` |
| 标准交期 | 倒排条长 / A 类延迟 | `fn_cli.py leadtime` |
| 供应状态 10 档 | **S1 内部**；无到位日 → unknown | `fn_cli.py supply-status` |

不要调用：合计可售（S2）、共用料争用（S3，除非用户同时要多单）。

## 平台降级

- 无 `query_metric` → 对象实例同一 `available_inventory_qty` + 同一 `warehouse_filter`
- 函数未上平台算子 → `tools/fn` / `fn_cli.py`，出参字段名与口径清单一致
