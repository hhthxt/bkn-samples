# OpenBKN 在线体验

在线路径与离线路径共享函数和业务口径。区别只有数据交接方式：第三方 Agent 自己调用官方 Context Loader，函数服务不查远端。

## 强制流程

```text
bkn_start_interaction
  → 官方 Context Loader 查询 BOM/库存/物料/PO/PR/MRP/预测
  → 保留每次查询的 bkn_receipt
  → 组装 resolved_context
  → 调用函数 Tool 或 Skill
  → 形成报告和 Action 提案
  → bkn_finish_interaction
```

`resolved_context` 至少包含 `knowledge_network_id`、`conversation_id`、`interaction_id`、带时区的 `captured_at`、`bkn_receipts` 和逻辑数据集行。

不要自行实现 HTTP、JSON-RPC、MCP 或 Context Loader 包装层；不要伪造 receipt；不要让函数服务直连绑定数据库；实时路径不能回退 CSV。

## 与离线结果对照

同一个场景应使用相同的产品、预测单、截止日和数量。比较 `snapshot_meta.input_digest`、S1/S2/S3 的业务结论和证据；允许的差异只能来自实时数据变化，并且必须在报告中说明。

详细数据集需求见 [第三方 Agent 数据交接说明](../第三方Agent数据交接说明.md)。
