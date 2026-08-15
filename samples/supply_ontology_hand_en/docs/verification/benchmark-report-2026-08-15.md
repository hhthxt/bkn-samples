# 第三方可验证动力层 P0 Benchmark 报告

日期：2026-08-15  
目标：`supply_ontology_hand` / localhost / `bd_public`

## 结论

本地动力层和平台对象更新成功；离线数值与场景验证均达到 100%，第三方对话 Playbook 行为盲测达到 100%。Context Loader 已通过严格名称为 `skills` 的对象类和 `public.skills` dataset 完成 3/3 Skill 召回。Action Gateway 已补齐；`close_monitor_task` 已通过标准 BKN 包推送、Action Dataset 绑定和平台 `action-type execute` 回归。

当前判定：**localhost 平台闭环通过，可进入客户/生态伙伴自然语言验收。**

## 1. localhost 更新结果

| 批次 | 结果 | 证据 |
|---|---|---|
| 指标 | 通过 | KN metrics = 8；8 个指标逐项更新并回读，范围和聚合字段匹配 |
| 函数 | 通过 | Toolbox = 13；13/13 enabled；新增 `open_forecast_count`、`backward_plan` |
| Skill | 通过 | 3/3 updated，3/3 published；`skills` 对象类绑定 `public.skills` dataset；`find_skills` 3/3 |
| Action | 通过 | 受控 Action Toolbox 3/3 enabled；创建与关闭 Action 已注册；平台 execute 1/1 成功，dry-run closed |

上传函数时平台拒绝了 11 个同名旧工具，但新增的 2 个缺失工具成功创建；没有删除或覆盖旧工具。OpenAPI 的数值型 `exclusiveMinimum` 已修正为 OpenAPI 3.0 兼容的 `minimum: 0` + `exclusiveMinimum: true`。

## 2. 离线正确性 Benchmark

| 指标 | 结果 |
|---|---:|
| metric accuracy | 1.00 |
| function accuracy | 1.00 |
| scenario accuracy | 1.00 |
| governance boundary accuracy | 1.00 |
| 独立断言总数 | 14 |
| 全量自动化测试 | 238 passed (including 6 orchestration-contract tests) |

独立评测覆盖产品/物料/供应商/订单/仓库、库存、预测需求、未关闭预测单，以及 S1 倒排、S2 可售、Action 仅提议不直接写入等边界。

The new orchestration contract verifies that the Agent passes its retained `conversation_id` / `interaction_id` through `bkn_context`, passes the existing `resolved_context` and dataset receipts directly to the Toolbox request, and rejects missing trace IDs, receipts, required datasets, or substitution policy before function invocation. The adapter does not persist, query, or execute Actions.

## 3. Action Gateway 验证

- 新增 `tools/action_gateway.py` 和 `tools/tests/test_action_gateway.py`，测试 `3 passed`。
- Gateway 仅绑定 `127.0.0.1:8766`，`/health`、`/ready` 正常，明确 `dry_run: true`。
- 修复长运行 Gateway 启动时冻结审批时钟的问题；测试可注入固定时间，生产请求按当前时间校验凭证。
- 受控行动 Toolbox：`784f5775-ba02-4c4b-8fbf-ac0920b9df8c`，3/3 工具 enabled。
- 直连 localhost 回归：`create_monitor_task` 返回 200/risk，随后 `close_monitor_task` 返回 200/closed，均为 `dry_run: true`。
- 平台 Action 回归：execution `d9vsabih1cbs73ertt90`，`completed`，`success_count=1`，目标 `task-platform-close-2`，结果 `task_status=closed`，`dry_run=true`。
- 关键契约修复：`action_type=modify`、`impact_contracts.expected_operation=modify`；监控任务对象绑定 `public.sc_plan_monitor_task`；移除 PostgreSQL 资源不支持的 `exists` 条件，使用 `_instance_identities` 定位实例。
- 无批准凭证：平台 Toolbox 返回 `approval_required`。
- 有效人工批准凭证：平台 Toolbox 返回 `200`，回执含 `task_id`、`task_status`、`dry_run: true`。
- KN 既有创建监控任务 Action 已绑定到该 Toolbox；新增关闭 Action 的当前平台 POST 接口返回“请求体为空 / No action type was passed in”，未产生对象，因此没有伪造通过。

## 4. 第三方视角盲测

盲测脚本：`tools/benchmark_third_party.py`

- 只抽取题号和业务问题，共 89 道输入题；不读取参考答案字段。
- Playbook 6/6 通过，准确率 1.00：
  - 不完整输入被转成澄清字段；
  - 补齐上下文后先返回 S1 证据；
  - S2 只能在 S1 审阅后继续；
  - Action 先提议，不直接写入；
  - 缺少人工批准凭证时拒绝执行；
  - 批准后返回可追踪的 dry-run 回执。

### 在线公开入口观察

通过官方 `bkn_start_interaction` 启动 Interaction，使用 `object_type_id=skills` 已返回 3 个已发布 Skill；使用 `skill_query=backward planning` 可精确返回 1 个。此前真实业务对象类会报 `ObjectTypeNotFound`，现已改为平台约定的 Skill 注册对象类。schema 搜索也能看到 `Skills`/`skills` 对象类和 `public.skills` 资源。

## 5. 未放行项

1. `create_pr_decision` 还需要对应 Action Dataset/对象类；本次未越过该 Dataset 门禁。
2. 由客户/生态伙伴执行一轮真实的“自然语言问题 → 澄清 → S1/S2/S3 → Action 提议 → 人工确认”验收，记录 Trace、澄清轮次、证据完整性和误触 Action 次数。
