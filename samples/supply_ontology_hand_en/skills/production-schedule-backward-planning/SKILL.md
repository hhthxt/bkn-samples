---
name: production-schedule-backward-planning_supply_ontology_hand_en
description: >
  Use when performing BOM-level production schedule backward planning (齐套倒排),
  material need-by dates, A/B delay classification, or supply-status diagnosis
  against a demand end date on knowledge network supply_ontology_hand.
---

# 生产计划倒排 · 齐套诊断（S1）

> OpenBKN 知识类 Skill。公式以体验包 `docs/能力口径清单.md` §2 为准，本包只编排指标、Toolbox 函数和行动。  
> 函数工具箱：`供应链计算函数工具箱`（`71600d21-c9f6-4336-bfbf-95bfb3654674`）。`tools/fn_cli.py` 仅作离线调试。

## Skill Card

| 字段 | 值 |
|------|-----|
| `bkn_scope` | `supply_ontology_hand` |
| `business_goal` | 按需求截止日完成 BOM 齐套倒排与交期风险诊断 |
| `user_persona` | PMC / 计划员 |
| `trigger` | 齐套倒排、生产计划倒排、A/B 延迟、物料到位时间 |
| `required_metrics` | 库存可用量（仓预设 `production_available`）；（对照）预测需求量合计 |
| `required_functions` | **生产计划齐套倒排**（`backward_plan`）；对照可用 **BOM 清单** / **子料分层库存** / **标准交期** |
| `required_toolbox` | `供应链计算函数工具箱`；优先调用 `生产计划齐套倒排` |
| `open_parameters` | `product_query`、`forecast_id`、`demand_end`、`demand_qty`、`warehouse_scope?`、`substitute_enabled`、`report_grain?` |
| `callable_actions` | 仅建议 `create_monitor_task` 或采购申请决策；须**人工确认**后才允许写 Dataset；禁止自动 `initiate_po`；**不创建 ERP** PR/PO |

不要调用：合计可售（S2）、共用料争用（S3，除非用户同时要多单）。无截止日不定论。监控目标只能是**一个产品 + 一张需求预测**。

## 数据交接（强制）

Agent 直接调用**官方 Context Loader**。不要让函数服务取数。本场景按 `backward_plan` 合同查询 `forecast`、`bom`、`material`、`inventory`、`purchase_order`、`purchase_request`、`mrp`。

1. 先 `bkn_start_interaction`
2. 按合同查询所需数据集，**只查询一次**，保留每份 `bkn_receipt`
3. 内联 `resolved_context` 调用函数 Tool；**函数服务不查询**
4. 结束时 `bkn_finish_interaction`

- **禁止伪造** receipt
- **禁止 CSV** 作为运行时输入
- 合同见 `docs/第三方Agent数据交接说明.md`

## 函数调用

平台执行时必须优先调用 Toolbox Tool `生产计划齐套倒排`（`backward_plan`），不在 Skill 内重写公式。只有 Toolbox 不可用且明确处于离线验收时，才使用以下 CLI：

在体验包 `tools/` 下：

```bash
python3 fn_cli.py backward-plan \
  --product 382-000005 \
  --forecast-id <id> \
  --demand-end 2026-05-14 \
  --qty 50 \
  --substitute no
```

Tool 与 CLI 出参字段名一致。

## 输入

- `knowledge_network_id`：默认 `supply_ontology_hand`
- `product_query`：必填
- `forecast_id`：必填，一张需求预测
- `demand_end`：YYYY-MM-DD，必填，且须与该预测单一致
- `demand_qty`：必填，且须与该预测单一致
- `warehouse_scope`：默认 `production_available`；允许 `finished_goods` / `all` / 显式仓列表，必须回显
- `substitute_enabled`：未给出则先问；未确认不得倒排
- `report_grain`：`summary`（默认）/ `full_tree`

未给出 `demand_end`：询问「请提供需求或生产截止日（YYYY-MM-DD）」，未确认前不分析。替代策略未确认同样不得下数量或交期结论。

## 编排（强制）

1. `resolve_context` — 官方 Context Loader **只查询一次**：一张需求预测、产品、BOM、物料主数据、库存、未关闭 PO/PR、MRP；保留 `bkn_receipt` 并内联 `resolved_context`  
2. `analyze` — 只调用 `backward_plan` / `生产计划齐套倒排`；只读已内联快照；**函数服务不查询**；**禁止**用合计可售代替齐套；不在 Skill 内重写公式  
3. `render_report` — Markdown；禁止再查远端  
4. `bkn_finish_interaction`  

仓名单必须来自预设展开（生产可用 7 仓：苏州半成品/成品/电子原料/无人机原料/装配原料 + 乌鲁木齐/哈尔滨成品仓）。禁止写死昆山/新疆或臆造仓名。

倒排规则见 `references/business-rules.md`。摘要：

1. L0：`end = demand_end`；`start = end - product_fixedleadtime`
2. 子件：`child_end = parent_start - 1`
3. 外购/委外 → 采购 LT；自制 → 生产 LT
4. 供给（倒排/10 档）= 可用 + **未关闭 PO 未清**；PR 未清只进档位
5. 无到位日 → `supply_status = unknown`
6. A 类：外购/委外，`start < today`，无 PO，库存不满足  
7. B 类：有 PO 且 `poDeliverDate > end`

## 完成门槛

1. `product_code` 与 `demand_end` 已解析  
2. BOM 非空（或明确「无 BOM」并终止）  
3. `warehouse_filter` 已回显  
4. 快照只生成一次  
5. 报告阶段远程查询次数为 0  

未满足 → 「数据前提不足，分析终止」，禁止交期承诺。

## 输出

1. `analysis_result`（见 `references/io-contract.md`）  
2. 完整 Markdown 报告（见 `references/report-spec.md`）  

结尾若需跟踪：只建议采购申请决策或监控任务，须**人工确认**后才允许写 Dataset，**不创建 ERP** PR/PO，不得自动 `initiate_po`。监控对象只能是一个产品 + 一张需求预测。

## 样例

- 产品 `382-000005`，截止日 `2026-05-14`
- CSV 离线：一层主料 9；`791-000013` 生产可用 1000；`791-000007` / `791-000015` 为 0

## 参考

- `references/business-rules.md`
- `references/io-contract.md`
- `references/report-spec.md`
- `references/kn-metrics.md`
- 口径 SSOT：体验包 `docs/能力口径清单.md`
