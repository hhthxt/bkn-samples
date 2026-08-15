# 输入输出契约：新需求覆盖（S3）

## 仅结构交（无数量）

```json
{
  "knowledge_network_id": "supply_ontology_hand",
  "products": ["382-000005", "P61-000351"],
  "shared_count": 28,
  "caliber": "structure_intersect_only"
}
```

## 有数量（争用）

```json
{
  "knowledge_network_id": "supply_ontology_hand",
  "demands": [
    {"product_code": "382-000005", "qty": 50},
    {"product_code": "P61-000351", "qty": 60}
  ],
  "substitute_enabled": false,
  "deduction_order": ["382-000005", "P61-000351"],
  "allocations": []
}
```

`deduction_order` 必须回显。产品级可售对照不得替代物料级 `shortage`。
