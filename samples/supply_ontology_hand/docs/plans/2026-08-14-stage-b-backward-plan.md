# Stage B S1 Backward Plan Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不封装 Context Loader、不连接远端和不读取运行时 CSV 的前提下，新增可第三方验证的 `backward_plan` 纯函数与第 13 个只读 Toolbox Tool。

**Architecture:** 第三方 Agent 先用官方 Context Loader 一次性取得 `forecast`、`bom`、`material`、`inventory`、`purchase_order`、`purchase_request`、`mrp`，以内联 `resolved_context` 调用函数。函数服务沿用阶段 A 的请求级 Snapshot 组装与 receipt 校验；倒排纯函数复用现有 BOM、库存、在途、提前期和供应状态函数，不复制公式。

**Tech Stack:** Python 3.11+、FastAPI、Pydantic、pytest、OpenAPI 3.0.3。

---

## 硬约束

1. 禁止新增 MCP/HTTP/CLI Context Loader 客户端。
2. 禁止函数服务发起远程查询或创建 Interaction。
3. 禁止运行时 CSV fallback；CSV 仅用于离线夹具。
4. `forecast_id` 必须对应内联 forecast 行，并与产品、截止日、需求量一致。
5. 主树仅采用主料 BOM；替代策略必须显式确认。
6. 日历日倒排；环路跳过并留 warning；超过 5000 节点拒绝。
7. 不读取业务问答测试集答案列。
8. 不修改 localhost 平台资产，不自动提交 git。

## Task 1：Snapshot 增加预测单索引和操作合同

**Files:**
- Modify: `tools/fn/snapshot.py`
- Modify: `tools/context/operation_contracts.py`
- Modify: `docs/payloads/resolved-context-contracts.json`
- Modify: `tools/tests/test_resolved_context.py`
- Modify: `tools/tests/test_operation_contracts.py`

### Step 1：写失败测试

- `build_snapshot()` 保留 `forecast` 行并按 `id` 建索引；
- `backward_plan` 必需数据集严格为 `forecast`、`bom`、`material`、`inventory`、`purchase_order`、`purchase_request`、`mrp`；
- Python 与 JSON 合同一致，共 13 个 operation。

### Step 2：验证 RED

在 `tools/`：

```bash
python3 -m pytest tests/test_resolved_context.py tests/test_operation_contracts.py -q
```

Expected: 缺 forecast Snapshot 字段和 `backward_plan` 合同而失败。

### Step 3：最小实现并验证 GREEN

```bash
python3 -m pytest tests/test_resolved_context.py tests/test_operation_contracts.py -q
```

## Task 2：建立倒排纯函数测试向量

**Files:**
- Create: `tools/tests/test_backward_plan.py`
- Create: `tools/tests/fixtures/backward_plan/README.md`

### Step 1：用最小合成 Snapshot 写失败测试

覆盖：

- 必填产品、forecast ID、日期、数量、替代策略；
- forecast 不存在或产品/日期/数量不一致拒绝；
- L0 `end=demand_end`、`start=end-product_fixedleadtime`；
- 子件 `end=parent.start-1`；
- 外购/委外采购 LT，自制生产 LT；
- 缺 LT 按 0，条长至少 1；
- 毛需求按路径累计单耗；
- 可用量、未关闭 PO 未清、PR 仅状态的现有口径；
- `unknown` 加 10 个供应状态；
- A/B 延迟，同料号保留最大延迟；
- `max_delay_days` 与 `can_deliver_on_time`；
- 环路跳过并返回 warning；
- 超过 5000 节点拒绝；
- BOM 空拒绝；
- `summary` 只保留根节点和风险/缺口节点，`full_tree` 返回完整树。

日期相关测试必须显式传入 `today`，不得依赖系统日期。测试预期只由规则公式和合成数据计算，不读取问答测试集答案。

### Step 2：验证 RED

```bash
python3 -m pytest tests/test_backward_plan.py -q
```

Expected: `fn.backward_plan` 不存在。

## Task 3：实现 `backward_plan` 纯函数

**Files:**
- Create: `tools/fn/backward_plan.py`
- Modify: `tools/fn/__init__.py`

### Step 1：实现最小算法

复用：

- `children_by_parent()` / `is_main_row()`
- `available_qty()` / `in_transit_qty()` / `po_open_rows()` / `has_mrp()`
- `leadtime_days()`
- `supply_status()`
- `resolve_warehouse_scope()`

输出：

```json
{
  "product_code": "...",
  "forecast_id": "...",
  "demand_qty": 0,
  "demand_end": "YYYY-MM-DD",
  "warehouse_filter": [],
  "substitute_enabled": false,
  "report_grain": "summary",
  "can_deliver_on_time": false,
  "max_delay_days": 0,
  "delay_a": [],
  "delay_b": [],
  "nodes": [],
  "node_count_total": 0,
  "gaps": [],
  "supply_status_summary": {},
  "warnings": []
}
```

每个 node 至少包含 material、parent、level、usage、gross requirement、start/end、lead time、available/in-transit、supply status、delay class、delay days、evidence。

### Step 2：验证 GREEN

```bash
python3 -m pytest tests/test_backward_plan.py tests/test_fn_core.py -q
```

## Task 4：暴露第 13 个只读 Tool

**Files:**
- Modify: `tools/fn_service.py`
- Modify: `tools/fn_cli.py`
- Modify: `tools/tests/test_fn_service.py`
- Create: `tools/tests/test_backward_plan_service.py`

### Step 1：写失败 API 测试

- operation ID 为 `backward_plan`，summary 为“生产计划齐套倒排”；
- 请求必填产品、forecast ID、日期、数量、替代策略；
- 不存在隐式远程查询参数；
- 缺必需 rows / receipt 拒绝；
- 成功响应有 `snapshot_meta.input_digest`；
- `summary` / `full_tree` 均可执行；
- OpenAPI 恰好 13 个业务 Tool。

### Step 2：验证 RED

```bash
python3 -m pytest tests/test_backward_plan_service.py tests/test_fn_service.py -q
```

### Step 3：最小实现并验证 GREEN

CLI 仅用于离线验收：

```bash
python3 fn_cli.py backward-plan \
  --product 382-000005 \
  --forecast-id 0000020520 \
  --demand-end 2026-01-31 \
  --qty 1015 \
  --substitute no
```

```bash
python3 -m pytest tests/test_backward_plan_service.py tests/test_fn_service.py -q
```

## Task 5：更新 S1 与第三方交接契约

**Files:**
- Modify: `skills/production-schedule-backward-planning/SKILL.md`
- Modify: `skills/production-schedule-backward-planning/references/io-contract.md`
- Modify: `skills/production-schedule-backward-planning/references/business-rules.md`
- Modify: `skills/production-schedule-backward-planning/references/report-spec.md`
- Modify: `docs/第三方Agent数据交接说明.md`
- Create: `tools/tests/test_backward_plan_docs.py`

### Step 1：写失败契约测试

验证：

- S1 优先调用 `backward_plan` / “生产计划齐套倒排”，不重写公式；
- 明确一个产品 + 一张 forecast；
- Agent 直接调用官方 Context Loader，只查询一次并内联 `resolved_context`；
- `backward_plan` 数据集合同完整；
- 无日期或替代策略未确认不得下结论；
- 只建议 PR 决策或监控任务，人工确认后才允许写 Dataset；
- 不创建 ERP PR/PO。

### Step 2：更新文档并验证

```bash
python3 -m pytest tests/test_backward_plan_docs.py tests/test_resolved_context_docs.py -q
```

## Gate B：只读倒排确认

在隔离副本执行：

```bash
python3 -m pytest tests -q
python3 export_fn_openapi.py
```

验收：

1. 全量 pytest 通过；
2. OpenAPI 3.0.3，恰好 13 个业务 Tool；
3. `backward_plan` 仅吃内联 `resolved_context`；
4. 无 MCP/HTTP/OpenBKN 客户端和运行时 CSV fallback；
5. 最小合成向量覆盖日期树、供应状态、A/B、环路和节点上限；
6. 原体验包和 localhost 平台均未在 Gate B 确认前改动。

Gate B 通过并取得确认后，才将隔离副本同步回原体验包。localhost Toolbox 上传仍属于后续独立门禁。
