# 输入输出契约：生产计划倒排（S1）

优先调用 Toolbox Tool `backward_plan`（生产计划齐套倒排）。Skill 不重写倒排公式。

## user_input

```json
{
  "knowledge_network_id": "supply_ontology_hand",
  "product_query": "382-000005",
  "forecast_id": "FC-001",
  "demand_end": "2026-05-14",
  "demand_qty": 50,
  "warehouse_scope": "production_available",
  "substitute_enabled": false,
  "report_grain": "summary"
}
```

- `product_query`、`forecast_id`、`demand_end`、`demand_qty`、`substitute_enabled` 必填
- 一个产品只对应一张需求预测
- `knowledge_network_id` 可缺省 → `supply_ontology_hand`
- 无日期或替代策略未确认：不得下齐套/交期结论

## resolved_context

由 Agent 调用官方 Context Loader 后内联，禁止 CSV 作为运行时输入。

```json
{
  "knowledge_network_id": "supply_ontology_hand",
  "conversation_id": "conv-example",
  "interaction_id": "int-example",
  "captured_at": "2026-08-14T13:00:00+00:00",
  "bkn_receipts": [],
  "rows": {
    "forecast": [],
    "bom": [],
    "material": [],
    "inventory": [],
    "purchase_order": [],
    "purchase_request": [],
    "mrp": []
  }
}
```

分析与报告阶段禁止再拉数。`backward_plan` 的数据集合同见 `docs/payloads/resolved-context-contracts.json`。

## analysis_result（摘要字段）

来自 `backward_plan`：

- `product_code` / `forecast_id` / `demand_end` / `demand_qty`
- `warehouse_filter`（必须回显）
- `can_deliver_on_time` / `max_delay_days`
- `delay_a` / `delay_b`
- `supply_status_summary`
- `gaps`
- `snapshot_meta.input_digest`
- 不得出现 S2 的 `total_sellable_qty` 作为齐套结论

监控建议若提出：目标只能是一个产品 + 一张需求预测；采购申请决策须人工确认；不创建 ERP PR/PO。
