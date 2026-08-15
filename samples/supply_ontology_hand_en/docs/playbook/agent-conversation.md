# Agent 对话接入 Playbook

业务故事 Runner 不是让客户直接操作的聊天机器人；它是 Agent 背后的确定性业务编排器。第三方 Agent 负责自然语言理解和对话，`ConversationPlaybook` 负责状态、参数完整性、Runner 调用和人工确认边界。

## 对话状态

```text
new
  → collecting_context
  → awaiting_s1_review
  → awaiting_s3_or_action
  → awaiting_human_confirmation
  → action_completed
```

## 推荐对话

```text
用户：客户要在 5 月 31 日前交付 3000 台 U00-000080，能不能接？

Agent：我需要确认对应的需求预测单，以及是否允许使用替代料。请提供 forecast_id，并确认替代料策略。

用户：forecast_id 是 0000023181，不允许替代料。

Agent：我先做生产计划倒排和齐套诊断。结果显示最大延迟 166 天，存在物料缺口，因此不能按期承诺。下面是关键证据……

用户：继续看可售能力。

Agent：当前成品库存加理论可产为 20 台。是否还要分析另一张需求对共享物料的争用？

用户：不用，创建监控任务。

Agent：我已生成监控任务提案，但尚未执行。任务是一产品一预测单，包含 57 个物料证据节点。请人工确认并提供批准凭证。

用户：确认。

Agent：没有有效批准凭证，我不能执行写入。请由批准网关签发绑定该提案的凭证。
```

## Agent 与 Playbook 的结构化交接

Agent 传入事件，而不是让模型直接拼接 Action SQL：

```json
{
  "type": "provide_context",
  "product": "U00-000080",
  "forecast_id": "0000023181",
  "demand_end": "2026-05-31",
  "demand_qty": 3000,
  "substitute_enabled": false
}
```

继续步骤：

```json
{"type": "continue", "step": "s2"}
```

补充 S3：

```json
{
  "type": "continue",
  "step": "s3",
  "demands": [
    {"product_code": "U00-000080", "qty": 3000},
    {"product_code": "382-000005", "qty": 10}
  ]
}
```

提出行动和执行行动必须分成两轮：

```json
{"type": "propose_action", "action": "create_monitor_task"}
```

只有批准网关返回与提案 hash、Interaction、Action 类型和幂等键匹配的凭证后，才允许：

```json
{
  "type": "confirm_action",
  "action": "create_monitor_task",
  "approval_token": "<approved-token>"
}
```

## Agent 必须遵守的规则

## Orchestration Skill calls

When the Agent recalls S1/S2/S3, the Skill returns an orchestration contract rather than an independent shell script. The Agent retains the two Interaction IDs, retrieves evidence once through Context Loader, passes `resolved_context` unchanged to the Toolbox function, and renders the report according to the Skill.

```text
Skill contract
→ Context Loader (once)
→ resolved_context + bkn_context
→ Toolbox function
→ Agent report
```

The function Toolbox is callable; the Agent should submit `resolved_context` through the OpenBKN Toolbox Tool interface and must not substitute an offline CLI result for online evidence.

- 缺少产品、预测单、数量、截止日或替代策略时先追问，不猜测；
- 不把 S1 的风险直接改写成客户承诺；
- 不把成品库存、理论可产、合计可售和齐套净需求混为一谈；
- 不在用户只说“建议一下”时执行 Action；
- 不使用普通“确认”文本代替批准凭证；
- 报告中保留 `snapshot_meta`、证据、口径和缺失前提；
- 在线路径由 Agent 自己查询 Context Loader，函数服务不代查、不回退 CSV。
