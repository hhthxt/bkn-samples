# localhost 动力层分批变更清单

更新时间：2026-08-15

## 当前基线

目标知识网络：`supply_ontology_hand`（业务域 `bd_public`）

| 层 | localhost 当前 | 本地合同 | 计划 |
|---|---:|---:|---|
| 指标 | 8 | 8 | 用本地载荷逐项回写并查询验收 |
| 函数 | 11 个工具 | 13 个函数 | 上传完整 OpenAPI，确认 13 个 operationId |
| Skill | 3 个已发布 + `skills` 对象类 | 3 个 | dataset 注册并通过 `find_skills` 召回 |
| Action | 3 个 KN Action | 3 个本地 dry-run Action | Gateway/Toolbox 已就绪；create→close 已通过平台 execute |

## 分批顺序

### Batch M：指标

- 目标：8 个指标的名称、口径、对象范围、聚合字段与本地目录一致。
- 验收：`metric list` 数量为 8；逐项按名称匹配；`metric validate` 通过；查询结果可追溯到 KN 对象。
- 第三方检查：问题使用业务名称即可完成，不要求客户知道内部 metric ID。

### Batch F：函数

- 目标：函数 Toolbox 有 13 个公开 operationId：`bom_list`、`bom_shared_list`、`layered_inventory`、`substitute_status`、`theoretical_build`、`total_sellable`、`kitting_net_demand`、`shared_contention`、`max_build_without_po`、`leadtime_days`、`supply_status`、`open_forecast_count`、`backward_plan`。
- 验收：Toolbox 回读为 published；13 个工具均可见；入口参数以 `resolved_context` 为核心；不暴露 ERP 写入。
- 第三方检查：先自然语言描述业务目标，再按 Agent 澄清问题提供产品/预测单/日期，不能要求客户拼内部函数名。

### Batch S：Skill

- 目标：三个 Skill 包与本地源目录同步，仍为 published。
- 验收：回读 Skill 内容索引，确认业务边界、证据要求、Action 人工确认门槛和“不创建 ERP PR/PO”约束存在。
- 第三方检查：Skill 能把不完整输入转成最少澄清问题，并给出可解释的 S1/S2/S3 下一步。

### Batch A：Action

- 目标：`create_pr_decision`、`create_monitor_task`、`close_monitor_task` 均具备可验证合同。
- 前置：Action Gateway `/ready` 可达，且平台支持目标 Action 类型的注册/更新。
- 验收：只做 dry-run；无人工批准凭证不得写入；批准凭证绑定 proposal hash、interaction、action type、审批人、过期时间和幂等键；不写 ERP。
- 当前状态：Action Gateway 已绑定 `127.0.0.1:8766` 并通过 `/ready`；3/3 Toolbox 工具 enabled；创建与关闭监控 Action 均已注册，平台 execute 已完成 `1/1` 成功回执。采购申请决策仍等待 Action Dataset/对象类门禁。
- 关闭函数已修复长运行时审批时钟冻结问题；平台执行使用 `modify` 合同、已绑定 `public.sc_plan_monitor_task`，并由 `_instance_identities` 定位目标实例。

### Batch S 补充：Skill dataset 注册

- Catalog：`supply-demo-hand` 发现 `public.skills`，resource id=`d9vre9llgf6s73e0nes0`。
- KN 对象类：`skills`（兼容对象类 `Skills`），绑定上述 resource；字段包含 `skill_id`、`name`、`description`、`skill_query`。
- Context Loader：同一 Interaction 下无关键词返回 3/3；`backward planning` 返回 1/1。

## 盲测原则

盲测执行者只读取题目、用户角色、可见上下文和公开入口，不读取测试集的参考答案列。报告记录任务完成率、澄清轮次、事实/口径正确率、证据完整率、误触 Action 次数、人工确认遵守率和第三方可操作性阻塞点。
