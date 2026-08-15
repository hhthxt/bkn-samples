# POC API 验证报告

日期：2026-08-15  
环境：`https://poc.openbkn.ai`  
模式：Agent API / CLI

## 已通过

- 中文 KN `supply_ontology_hand` 导入并回读成功。
- 英文 KN `supply_ontology_hand_en` 导入并回读成功。
- 两个 KN 均为 15 个对象类、19 个关系、3 个行动。
- 当前环境 embedding 动态解析成功。
- 中文 KN 的 10 个可用对象类资源绑定成功；销售订单对象因缺少同构 `sales_order` 表暂未绑定。
- 7 个非销售订单指标注册成功，7 个逻辑属性绑定成功。

## 未通过

### 线上 sample 数据推送

`bkn create-from-csv` 在 POC 的当前 Catalog 上调用数据流接口返回 HTTP 404，未形成可供 sample 使用的隔离数据资源。需要一个可写入的物理 Catalog，或启用 POC 的 CSV 数据流 API。

### 指标盲测

指标定义能执行，但查询到了 POC 现有 ERP 数据，不是 sample CSV，因此 11 个非销售订单用例全部数值不匹配。例如：

| 指标 | sample 期望 | POC 当前返回 |
|---|---:|---:|
| 产品总数 | 30 | 431 |
| 物料总数 | 3497 | 14283 |
| 供应商总数 | 230 | 3372 |
| 未关闭预测单数 | 90 | 568 |

这不是指标公式错误，而是数据源未切换到 sample 快照。

## 下一步放行条件

1. 提供可写入的物理 Catalog，使用 `hand_` 前缀推送 12 份 sample CSV；
2. 扫描并核对资源行数；
3. 将 11 个对象类绑定到 `hand_` 资源；
4. 补齐 `sales_order` 后注册第 8 个指标并绑定销售订单逻辑属性；
5. 重新运行指标盲测、函数、Skill、Playbook 和 Action 验证；
6. 全部通过后才允许推送 GitHub 主线。
