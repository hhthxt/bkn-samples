# 输入输出契约：产品可售能力（S2）

## user_input

```json
{
  "knowledge_network_id": "supply_ontology_hand",
  "product_query": "382-000005",
  "substitute_enabled": false
}
```

`substitute_enabled` 缺省时必须先问。

## analysis_result

```json
{
  "knowledge_network_id": "supply_ontology_hand",
  "product_code": "382-000005",
  "fg_qty": 534,
  "theoretical_build_qty": 0,
  "total_sellable_qty": 534,
  "substitute_enabled": false,
  "finished_goods_filter": ["苏州成品仓", "乌鲁木齐成品仓", "哈尔滨成品仓"],
  "production_filter": [
    "苏州半成品仓",
    "苏州成品仓",
    "苏州电子原料仓",
    "苏州无人机原料仓",
    "苏州装配原料仓",
    "乌鲁木齐成品仓",
    "哈尔滨成品仓"
  ],
  "include_in_transit": false
}
```

字段名必须与函数出参一致。报告须声明：不是交期承诺。
