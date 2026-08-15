# 第三方 Agent 编排型 Skill 设计

日期：2026-08-15

## 目标

将供应链 Skill 定义为“编排契约”，由第三方 Agent 负责理解问题、补齐参数、调用受管数据查询和函数；由 Toolbox 函数执行确定性计算；由 Agent 按 Skill 规则生成报告并提出受控 Action。

## 职责边界

| 组件 | 职责 | 禁止事项 |
|---|---|---|
| Skill | 声明触发条件、必需输入、数据集合同、函数 ID、输出格式和治理边界 | 不直接查询数据；不在 Skill 内重写计算公式 |
| 第三方 Agent | 保存并透传 `conversation_id`、`interaction_id`；调用 Context Loader；组装 `resolved_context`；调用 Toolbox；生成报告 | 不绕过受管上下文；不凭空计算或伪造 receipt；不自动执行 Action |
| Context Loader | 按当前 Interaction 查询一次权威数据并返回证据回执 | 不接受猜测的生命周期 ID |
| Toolbox 函数 | 只消费已解析的 `resolved_context`，执行确定性计算并返回结果 | 不自行连接数据库或再次查询远端数据 |
| Action | 在人工批准后执行受控写入 | 未确认不得创建、修改或关闭业务对象 |

## 调用流程

1. Agent 调用 `bkn_start_interaction`，保存平台返回的两个 ID。
2. Agent 根据 Skill 契约调用 Context Loader，查询预测、产品、BOM、物料、库存、采购和 MRP；保存每份 `bkn_receipt`。
3. Agent 将数据快照、查询回执和业务参数组装为 `resolved_context`，调用 `backward_plan`。
4. Toolbox 只基于 `resolved_context` 计算，不再查询数据库；函数回执归属于同一 `interaction_id`。
5. Agent 根据 Skill 的报告契约生成结论；若需要后续行动，只输出 Action 提议和审批要求。
6. Agent 调用 `bkn_finish_interaction`，提交完整答案和证据状态。

`resolved_context` 是函数调用输入，不需要另建持久化存储。Agent 已保存的 `conversation_id`、`interaction_id` 也不需要复制到新的业务存储；只需在每次受管工具调用的 `bkn_context` 中原样透传。

## 执行接口决策

S1 属于编排型 Skill，不强制使用 `execute_skill`。`execute_skill` 仅适用于 Skill 明确声明了可执行 `entry_shell` 的脚本型 Skill。编排型 Skill 通过 `find_skills` / `get_skill_content` 获取契约，再由第三方 Agent 按上述流程执行。

POC 已支持函数 Toolbox 调用；需要区分 Context Loader 的 MCP 工具目录和 OpenBKN Execution Factory REST Proxy。第三方 Agent 应在保留 Interaction 上下文的前提下，通过 `/api/agent-operator-integration/v1/tool-box/{box_id}/proxy/{tool_id}` 提交 `resolved_context` 与业务参数。Agent 不需要知道 OpenAPI Toolbox 后端的 `FUNCTION_SERVICE_URL`；该地址由管理员配置。`execute_skill` 只用于有明确 `entry_shell` 的脚本型 Skill，不作为 S1 的函数调用入口。

## 错误与治理

- 缺少 `demand_end`、`forecast_id`、`demand_qty` 或替代料策略：先澄清，不调用函数。
- 任一必需数据集为空、BOM 为空或 receipt 不完整：终止分析，不给交付承诺。
- 函数调用失败：保留原始错误并结束当前 Interaction，不降级为离线数据或手工计算。
- Action 缺少人工批准凭证：返回 `approval_required`，不写入 Dataset。

## 验收标准

- Skill 可被严格名称为 `skills` 的对象类召回。
- Agent 能在同一 Interaction 内完成数据查询、`resolved_context` 函数调用和报告闭环。
- 函数服务没有远端查询行为，结果可由回执追踪。
- Action 在无批准和有批准两种情况下分别表现为拒绝和 dry-run/受控执行。
- 中文、英文 sample 的手册、契约测试和 POC 报告保持一致。
