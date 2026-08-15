# Stage A Inline Resolved Context Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将现有 11 个函数 Tool 从服务启动时 CSV 快照改为由第三方 Agent 查询 Context Loader 后内联传入 `resolved_context`，并新增安全的未关闭预测单数 Tool。

**Architecture:** 第三方 Agent 直接使用官方 Context Loader 工具管理查询和 Trace；函数服务不包含 AppKey、MCP Client、Context Loader Provider 或远程查询。函数服务只校验 `resolved_context`、组装 Snapshot、计算并返回输入摘要哈希。

**Tech Stack:** Python 3.11+、FastAPI、Pydantic、pytest、OpenBKN Toolbox。

**Design SSOT:** `docs/第三方可验证动力层P0优化设计.md`

---

## 硬约束

1. 禁止新增 MCP/HTTP/CLI Context Loader 客户端。
2. 禁止函数服务发起任何远程查询。
3. 禁止函数服务创建或关闭 Interaction。
4. 禁止运行时 CSV fallback。
5. CSV 仅用于测试夹具生成。
6. 不修改 localhost 平台资产。
7. 严格 TDD；先看到测试按预期失败。
8. 不自动提交 git。

## Task 1：ResolvedContext 合同与 Snapshot 组装

**Files:**
- Create: `tools/context/__init__.py`
- Create: `tools/context/contract.py`
- Create: `tools/context/assembler.py`
- Create: `tools/tests/test_resolved_context.py`
- Modify: `tools/fn/snapshot.py`

### Step 1：写失败测试

测试至少覆盖：

- `ResolvedContext` 必须包含正确 KN ID；
- 必须包含 `conversation_id` 和 `interaction_id`；
- 必须包含 UTC/带时区 `captured_at`；
- `rows` 按逻辑数据集分组；
- 非空远程数据集必须存在对应 `bkn_receipt`；
- 上下文超过配置时效返回 `context_stale`；
- `SnapshotEnvelope` 包含 `input_digest`；
- 相同规范化输入得到相同 SHA-256；
- 行顺序或数值变化会改变摘要；
- `build_snapshot()` 构建全部索引且不修改输入；
- `load_csv_snapshot(data_dir)` 不污染默认数据目录。

建议合同：

```python
@dataclass(frozen=True, slots=True)
class ResolvedContext:
    knowledge_network_id: str
    conversation_id: str
    interaction_id: str
    captured_at: datetime
    rows: Mapping[str, Sequence[Mapping[str, Any]]]
    bkn_receipts: tuple[Mapping[str, Any], ...]

@dataclass(frozen=True, slots=True)
class SnapshotEnvelope:
    snapshot: Snapshot
    snapshot_id: str
    captured_at: datetime
    knowledge_network_id: str
    conversation_id: str
    interaction_id: str
    source: Literal["openbkn", "offline_test"]
    bkn_receipts: tuple[Mapping[str, Any], ...]
    loaded_datasets: frozenset[str]
    input_digest: str
```

### Step 2：验证 RED

Working directory: `tools`

```bash
python3 -m pytest tests/test_resolved_context.py -q
```

Expected: 因 `context.contract` / `context.assembler` 不存在而失败。

### Step 3：最小实现

`ResolvedContextAssembler.assemble()`：

1. 校验 KN 和受管 ID；
2. 校验时间；
3. 校验 operation 所需数据集；
4. 校验 receipt；
5. 复制并规范化 rows；
6. 调用 `build_snapshot()`；
7. 对规范 JSON 计算 SHA-256；
8. 返回 Envelope。

receipt 只做存在性和 Interaction 一致性校验，不伪造服务端签名校验。

### Step 4：验证 GREEN

```bash
python3 -m pytest tests/test_resolved_context.py tests/test_fn_core.py -q
python3 -m pytest tests -q
```

Expected: 全部通过。

## Task 2：定义每个函数的数据需求合同

**Files:**
- Create: `tools/context/operation_contracts.py`
- Create: `tools/tests/test_operation_contracts.py`
- Create: `docs/payloads/resolved-context-contracts.json`

### Step 1：写失败测试

为每个 operation 定义最小数据集：

| Operation | 必需 rows |
|---|---|
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

测试：

- 12 个 operation 全覆盖；
- 不允许未知数据集；
- 缺数据集列出精确缺失项；
- 合同 JSON 与 Python 定义一致；
- 合同不包含 Context Loader API 参数或 SQL。

### Step 2：验证 RED

```bash
python3 -m pytest tests/test_operation_contracts.py -q
```

### Step 3：实现合同

仅描述函数输入所需逻辑数据集和核心字段。查询方式由 Skill 负责。

### Step 4：验证 GREEN

```bash
python3 -m pytest tests/test_operation_contracts.py -q
```

## Task 3：函数服务改为内联 resolved_context

**Files:**
- Modify: `tools/fn_service.py`
- Create: `tools/service_dependencies.py`
- Create: `tools/tests/test_fn_service_runtime.py`
- Modify: `tools/tests/test_fn_service.py`

### Step 1：写失败测试

覆盖：

- 导入 `fn_service` 不调用 `load_csv_snapshot`；
- 每个业务请求在运行模式必须带 `resolved_context`；
- 缺上下文返回 `422 context_required`；
- 缺数据集返回 `422 snapshot_incomplete`；
- 缺 receipt 返回 `422 receipt_required`；
- 过期上下文返回 `409 context_stale`；
- 成功响应包含 `snapshot_meta` 和 `input_digest`；
- 函数服务源码不导入 MCP/HTTP/OpenBKN 客户端；
- `/health` 不访问外部服务；
- `/ready` 只检查运行模式和合同版本，不检查 OpenBKN；
- `/health`、`/ready` 不进入 OpenAPI；
- 显式 `offline_test` 模式可由测试注入 CSV resolved context；
- 运行模式绝不自动读取 CSV。

### Step 2：验证 RED

```bash
python3 -m pytest tests/test_fn_service_runtime.py -q
```

### Step 3：实现请求合同

新增 Pydantic 模型：

```python
class ResolvedContextRequest(BaseModel):
    knowledge_network_id: str
    conversation_id: str
    interaction_id: str
    captured_at: datetime
    bkn_receipts: list[dict[str, Any]]
    rows: dict[str, list[dict[str, Any]]]
```

所有业务请求增加必填：

```python
resolved_context: ResolvedContextRequest
```

endpoint 流程：

1. 根据 operation ID 读取数据需求合同；
2. assemble；
3. 调用现有纯函数；
4. 合并 `snapshot_meta`；
5. 返回。

### Step 4：迁移现有服务测试

测试使用公共 fixture 从 CSV 生成 `offline_test` 格式上下文，避免每题复制大 payload。

### Step 5：验证 GREEN

```bash
python3 -m pytest tests/test_fn_service.py tests/test_fn_service_runtime.py -q
python3 -m pytest tests -q
```

Expected: 全部通过。

## Task 4：新增安全未关闭预测 Tool

**Files:**
- Create: `tools/fn/forecast.py`
- Modify: `tools/fn/__init__.py`
- Modify: `tools/fn_service.py`
- Modify: `tools/export_fn_openapi.py`
- Create: `tools/tests/test_forecast.py`
- Modify: `tools/tests/test_fn_service.py`

### Step 1：写失败测试

覆盖：

- 固定排除 `closestatus_title == 已关闭`；
- 可选 `product_code` 追加过滤；
- API 不存在 `include_closed`；
- 结果与输入 forecast rows 独立计数一致；
- 缺 forecast rows/receipt 拒绝；
- 返回快照摘要。

### Step 2：验证 RED

```bash
python3 -m pytest tests/test_forecast.py -q
```

### Step 3：实现

```python
def open_forecast_count(
    forecast_rows: list[dict],
    *,
    product_code: str | None = None,
) -> dict:
    ...
```

OpenAPI：

- operation ID: `open_forecast_count`
- summary: `未关闭预测单数`

### Step 4：导出和验证

```bash
python3 -m pytest tests -q
python3 export_fn_openapi.py
```

Expected:

- 全部测试通过；
- OpenAPI 3.0.3；
- 12 个业务 Tool；
- 无 `type: null`；
- 无 Context Loader/MCP server 地址。

## Task 5：第三方 Agent 查询交接说明

**Files:**
- Create: `docs/第三方Agent数据交接说明.md`
- Modify: `skills/production-schedule-backward-planning/SKILL.md`
- Modify: `skills/demand-fulfillment-capacity-analysis/SKILL.md`
- Modify: `skills/demand-fulfillment-requirement-coverage-analysis/SKILL.md`
- Create: `tools/tests/test_resolved_context_docs.py`

### Step 1：写文档契约测试

验证文档和三个 Skill 均明确：

- Agent 直接调用官方 Context Loader；
- 一轮先 `bkn_start_interaction`；
- 查询后保留 receipts；
- 同一场景只查询一次；
- 内联传入 `resolved_context`；
- 函数服务不查询 Context Loader；
- 最终调用 `bkn_finish_interaction`；
- 禁止伪造 receipt；
- 禁止 CSV fallback；
- 各 operation 查询所需数据集与合同一致。

### Step 2：验证 RED

```bash
python3 -m pytest tests/test_resolved_context_docs.py -q
```

### Step 3：写第三方说明

至少给出 S2 示例流程：

```text
start interaction
→ 查询产品/BOM/库存
→ 组装 resolved_context
→ 调用 total_sellable
→ finish interaction
```

示例不得包含真实 AppKey。

### Step 4：验证 GREEN

```bash
python3 -m pytest tests/test_resolved_context_docs.py -q
python3 -m pytest tests -q
```

## Gate A 验收

展示：

1. 本地文件 diff；
2. RED/GREEN 证据；
3. 全量 pytest；
4. 12 Tool OpenAPI；
5. 函数服务源码无 MCP/HTTP/OpenBKN 客户端的静态检查；
6. 运行模式无 CSV fallback；
7. `resolved_context` 和 receipt 错误样例；
8. 第三方 Agent 数据交接说明。

Gate A 通过后才允许：

- 将隔离副本变更同步到原工具包；
- 规划阶段 B；
- 后续更新 localhost Toolbox。

本阶段不执行任何 localhost 平台写操作。

