# 指标目录

| ID | 口径 | 本地样例值 |
|---|---|---:|
| `product_count` | 产品编码去重 | 30 |
| `material_count` | 物料编码去重 | 3497 |
| `supplier_count` | 供应商编码去重 | 230 |
| `sales_order_count` | 销售订单号去重 | 800 |
| `warehouse_count` | 库存仓库去重 | 29 |
| `available_inventory_qty` | 可用库存数量，按产品/仓范围过滤 | 382-000005 成品仓 534 |
| `forecast_demand_qty` | Open forecast quantity total | 56340 |
| `open_forecast_count` | Open forecast count excluding closed rows | 90 |

本地入口：`tools/metrics.py`。每个结果包含 metric ID、过滤条件、来源和证据行数。在线指标载荷见 `docs/payloads/`，平台口径不能被本地展示层悄悄改写。
