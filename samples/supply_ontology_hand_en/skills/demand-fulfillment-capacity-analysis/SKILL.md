---
name: demand-fulfillment-capacity-analysis
description: >
  Use when analyzing how many finished units can be sold now (成品仓 + 理论可产)
  on knowledge network supply_ontology_hand. Not a delivery-date promise.
---

# 需求承接 · 产品可售能力（S2）

> 只编排指标/函数并出报告，不另发明可售公式。口径：体验包 `docs/能力口径清单.md` §2。  
> 三个数分开：**理论可产 ≠ 合计可售 ≠ 齐套净需求**。本 Skill 只回答合计可售。
> 函数工具箱：`供应链计算函数工具箱`。部署时按工具箱名称解析当前 `published` 实例；不得在 Skill 中固化环境 UUID。

## Skill Card

| 字段 | 值 |
|------|-----|
| `bkn_scope` | `supply_ontology_hand` |
| `trigger` | 现在最多能卖多少、可售能力、理论可产+成品库存 |
| `required_metrics` | 库存可用量（成品仓 `finished_goods` + 生产仓 `production_available`） |
| `required_functions` | **BOM 清单**；**替代料状态**；**理论可产**；**合计可售** |
| `required_toolbox` | 优先调用 `BOM清单`、`替代料状态`、`理论可产`、`合计可售` |
| `open_parameters` | `product_query`、`substitute_enabled`、`warehouse_scope?` |

不要调用：净需求/齐套、供应状态 10 档、共用料争用 / S3。在途 PO 可作对照，**不得**加入合计可售。

## 数据交接（强制）

Agent 直接调用**官方 Context Loader**。不要让函数服务取数。本场景最少查询 `bom`、`inventory`（`total_sellable` / `theoretical_build` / `substitute_status`）。

1. 先 `bkn_start_interaction`
2. 按合同查询所需数据集，**只查询一次**，保留每份 `bkn_receipt`
3. 内联 `resolved_context` 调用函数 Tool；**函数服务不查询**
4. 结束时 `bkn_finish_interaction`

- **禁止伪造** receipt
- **禁止 CSV** 作为运行时输入
- 合同见 `docs/第三方Agent数据交接说明.md`

## 口径（禁止改写）

- `理论可产 = MIN(FLOOR(生产可用 / 单耗))`，不加成品、不加在途；替代组内 **MAX**；缺省展开到叶子主料
- `合计可售 = 成品仓可用 + 理论可产`
- 未给出 `substitute_enabled` → 先问再算；未确认返回不能算

## 函数调用

平台执行时优先调用 Toolbox Tool，不在 Skill 内重写公式。以下 CLI 只用于离线验收：

```bash
cd tools
python3 fn_cli.py bom-list --product U00-000151 --depth 1
python3 fn_cli.py substitute --product 382-000005
python3 fn_cli.py theoretical --product 382-000005 --substitute no
python3 fn_cli.py sellable --product 382-000005 --substitute no
```

CSV 快照：`382-000005` 成品仓约 **534**，无替代时理论可产 **0**，合计可售 **534**；`U00-000151` 成品仓约 **3800**。

## 输入

- `knowledge_network_id`：默认 `supply_ontology_hand`
- `product_query`：必填
- `substitute_enabled`：未给出则询问「是否启用替代料核算？（是/否）」
- 仓范围：成品部分固定 `finished_goods`（3 仓），理论可产用 `production_available`（7 仓）；须回显，不得写死昆山仓

## 编排

1. `resolve_context` — 官方 Context Loader **只查询一次**：产品、BOM、成品仓可用、生产仓可用、替代组；保留 `bkn_receipt` 并内联 `resolved_context`  
2. `analyze` — 调用理论可产 + 合计可售；只读已内联快照；**函数服务不查询**  
3. `render_report` — Markdown；禁止再查远端；**声明这不是交期承诺**  
4. `bkn_finish_interaction`

## 完成门槛

1. 产品已解析且 BOM 非空（或明确无 BOM 并终止）  
2. `substitute_enabled` 已确认  
3. 成品仓名单与生产仓名单均回显  
4. 出参含 `fg_qty` / `theoretical_build_qty` / `total_sellable_qty`  
5. 报告阶段远程查询次数为 0  

## 输出

1. `analysis_result`：见 `references/io-contract.md`  
2. 完整 Markdown：见 `references/report-spec.md`

## 参考

- `references/business-rules.md`
- `references/io-contract.md`
- `references/report-spec.md`
