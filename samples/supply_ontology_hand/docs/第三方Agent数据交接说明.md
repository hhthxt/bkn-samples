# 第三方 Agent 数据交接说明

面向接入 `supply_ontology_hand` 函数工具箱的第三方 Agent。函数服务**不持有凭据、不查询远端、不读取 CSV**。Agent 必须自己调用**官方 Context Loader**，把结果以内联 `resolved_context` 交给函数。

**不要封装 Context Loader。** 不要再写一层 HTTP/JSON-RPC/SDK 去代理官方工具。直接使用宿主已提供的 Context Loader 工具。

## 责任边界

| 角色 | 允许 | 禁止 |
|------|------|------|
| 第三方 Agent | 调用官方 Context Loader；`bkn_start_interaction` / `bkn_finish_interaction`；组装 `resolved_context`；调用函数 Tool | 伪造 `bkn_receipt`；把 CSV 当作运行时数据源；让函数服务去查知识网络 |
| 函数服务 | 校验 `resolved_context`、组装 Snapshot、计算、返回 `snapshot_meta.input_digest` | 查询 Context Loader；创建/关闭 Interaction；运行时 CSV fallback |

## 强制流程

同一业务场景**只查询一次**。查询发生在函数调用之前；报告阶段不得再查远端。

```text
bkn_start_interaction
→ 官方 Context Loader 查询所需逻辑数据集（只查询一次）
→ 保留每份查询的 bkn_receipt
→ 组装 resolved_context
→ 调用函数 Tool（例如 total_sellable）
→ bkn_finish_interaction
```

规则：

1. 一轮对话先 `bkn_start_interaction`，拿到 `conversation_id` / `interaction_id`。
2. 按下方合同查询对象实例或资源行，把行写入 `resolved_context.rows.<dataset>`。
3. 每个非空远程数据集必须带对应 `bkn_receipt`，且 `interaction_id` 与本轮一致。
4. 把完整 `resolved_context` 内联进函数请求体。**函数服务不查询**。
5. 计算结束后 `bkn_finish_interaction`。
6. **禁止伪造** receipt。没有官方查询回执就不要调用函数。
7. **禁止 CSV** 作为运行时输入。CSV 只用于离线夹具和黄金对照，不进生产请求。

## 编排型 Skill 的执行方式

S1/S2/S3 是编排型 Skill，不要求通过 `execute_skill` 运行 shell 命令。第三方 Agent 先通过 `find_skills` / `get_skill_content` 读取 Skill 契约，再按契约调用 Context Loader 和 Toolbox。

Agent 已经保存的 `conversation_id`、`interaction_id` 不需要另建存储；每次调用时原样放入 `bkn_context`。Agent 已经取得的 `resolved_context` 也不需要再次持久化，直接作为 Toolbox 请求输入。

```text
find_skills / get_skill_content
→ Context Loader 查询一次并保存 receipt
→ Agent 组装 resolved_context
→ OpenBKN Toolbox REST Proxy(backward_plan, resolved_context + parameters)
→ Agent 按 Skill 输出契约生成报告
→ 有需要时提出 Action，等待人工确认
```

Skill 不自行查询、函数不自行查询，Agent 不得脱离快照重算或伪造证据。函数 Toolbox 已支持调用；不要把 Context Loader 的 MCP 工具列表当作 Toolbox 工具列表。S1 应通过 OpenBKN Execution Factory REST Proxy 提交 `resolved_context` 和业务参数，`execute_skill` 仅用于脚本型 Skill。Agent 不需要知道后端 `FUNCTION_SERVICE_URL`。

## `resolved_context` 形状

```json
{
  "knowledge_network_id": "supply_ontology_hand",
  "conversation_id": "<from bkn_start_interaction>",
  "interaction_id": "<from bkn_start_interaction>",
  "captured_at": "2026-08-14T13:00:00+00:00",
  "bkn_receipts": [
    {
      "dataset": "bom",
      "interaction_id": "<same interaction>",
      "query_type": "query_object_instance",
      "row_count": 12
    }
  ],
  "rows": {
    "bom": [],
    "inventory": []
  }
}
```

`captured_at` 必须带时区。默认时效 900 秒；超时函数返回 `context_stale`（HTTP 409）。

常见拒绝：

| 错误码 | 含义 |
|--------|------|
| `context_required` | 缺少 `resolved_context`，或 KN / 受管 ID 不合规 |
| `receipt_required` | 非空远程数据集没有归属本 Interaction 的 `bkn_receipt` |
| `snapshot_incomplete` | 缺少该 operation 的必需 `rows` 键 |
| `context_stale` | 超过允许时效 |
| `schema_mismatch` | 结构无法解析 |

## 各函数所需数据集

合同 SSOT：`docs/payloads/resolved-context-contracts.json`。Agent 只按逻辑数据集名取数，不要向函数服务描述 SQL 或 Context Loader 调用细节。

| operation | required_rows |
|-----------|---------------|
| `bom_list` | `bom` |
| `bom_shared_list` | `bom` |
| `layered_inventory` | `bom`, `inventory` |
| `substitute_status` | `bom`, `inventory` |
| `theoretical_build` | `bom`, `inventory` |
| `total_sellable` | `bom`, `inventory` |
| `kitting_net_demand` | `bom`, `inventory`, `purchase_order` |
| `shared_contention` | `bom`, `inventory`, `purchase_order` |
| `max_build_without_po` | `bom`, `inventory` |
| `leadtime_days` | `material` |
| `supply_status` | `material`, `inventory`, `purchase_order`, `purchase_request`, `mrp` |
| `open_forecast_count` | `forecast` |
| `backward_plan` | `forecast`, `bom`, `material`, `inventory`, `purchase_order`, `purchase_request`, `mrp` |

可选辅助数据集：`product`。`open_forecast_count` 固定排除 `closestatus_title == 已关闭`。`backward_plan` 对应 Tool 摘要「生产计划齐套倒排」，监控粒度为一个产品 + 一张需求预测。

## S2 示例：合计可售

场景：产品 `382-000005`，不启用替代。

1. `bkn_start_interaction`（知识网络 `supply_ontology_hand`）。
2. 官方 Context Loader 查询 `bom` 与 `inventory`（只查询一次），保留 `bkn_receipt`。
3. 组装 `resolved_context`，`rows.bom` / `rows.inventory` 放入本轮查询结果。
4. 调用 `total_sellable`：

```json
{
  "product": "382-000005",
  "substitute_enabled": false,
  "resolved_context": {
    "knowledge_network_id": "supply_ontology_hand",
    "conversation_id": "conv-example",
    "interaction_id": "int-example",
    "captured_at": "2026-08-14T13:00:00+00:00",
    "bkn_receipts": [
      {"dataset": "bom", "interaction_id": "int-example"},
      {"dataset": "inventory", "interaction_id": "int-example"}
    ],
    "rows": {
      "bom": [{"placeholder": "official Context Loader rows"}],
      "inventory": [{"placeholder": "official Context Loader rows"}]
    }
  }
}
```

5. 使用返回的 `fg_qty` / `theoretical_build_qty` / `total_sellable_qty` 与 `snapshot_meta.input_digest` 出报告。
6. `bkn_finish_interaction`。

示例不含任何凭据。函数服务不会替你补查；缺 `resolved_context` 会直接拒绝。
