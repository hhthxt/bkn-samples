# Third-Party Verifiable Power Layer P0 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
>
> **状态：已被修订。** 阶段 A 不再由函数服务访问 Context Loader。以
> `2026-08-14-stage-a-inline-resolved-context.md` 为阶段 A 的执行计划；
> 后续阶段在各自确认门禁前重新生成独立计划。

**Goal:** 将 `supply_ontology_hand` 动力层升级为第三方可安装、OpenBKN-only 实时取数、可追溯并可独立验收的指标、函数、Skill、Dataset 和 Action 工具包。

**Architecture:** 保留 `tools/fn` 纯函数核心，新增通过 Context Loader MCP 取数的 Provider 与请求级 Snapshot；新增安全预测计数和 S1 综合倒排 Tool；使用三张结构化表承接采购申请决策和产品 + 单张需求预测监控任务；Dataset 写入通过人工批准网关。

**Tech Stack:** Python 3.11+、FastAPI、Pydantic、官方 MCP Python SDK、pytest、OpenBKN Context Loader MCP、OpenBKN Toolbox、Vega Resource、PostgreSQL/MySQL。

**Design SSOT:** `docs/第三方可验证动力层P0优化设计.md`

---

## 执行约束

1. 本计划不是实施授权。
2. 每个阶段开始前必须展示该阶段文件与平台变更清单并取得确认。
3. 阶段 A、B 只改本地代码和文档，不修改 localhost 平台资产。
4. 阶段 C、D 先完成本地 dry-run，再申请 Dataset/BKN/Action 变更确认。
5. 阶段 E 的 localhost 注册、发布、索引重建必须单独确认。
6. 不创建真实 ERP PR/PO，不修改 ERP 生产计划。
7. 不读取 `docs/业务问答测试集.md` 的“参考答案”列。
8. 不自动创建 git commit；仅在用户明确要求时提交。

## 阶段 A：OpenBKN-only 只读运行时

### Task 1: 建立 Provider 合同与快照信封

**Files:**
- Create: `tools/providers/__init__.py`
- Create: `tools/providers/base.py`
- Create: `tools/tests/test_provider_contract.py`
- Modify: `tools/fn/snapshot.py`

**Step 1: 写失败测试**

覆盖：

```python
def test_snapshot_envelope_requires_openbkn_provenance():
    envelope = SnapshotEnvelope(
        snapshot=Snapshot(),
        snapshot_id="snap-1",
        captured_at="2026-08-14T13:00:00Z",
        knowledge_network_id="supply_ontology_hand",
        source="openbkn",
        conversation_id="conv-1",
        interaction_id="int-1",
        resource_receipts=[],
        loaded_datasets={"bom"},
    )
    assert envelope.source == "openbkn"
```

同时验证：

- 非 `openbkn/offline_test` 来源拒绝；
- 运行模式下缺少 Interaction 拒绝；
- `SnapshotPlan` 可表达产品、预测单、物料集合和数据集需求；
- `Snapshot` 建索引不修改输入行。

**Step 2: 验证测试失败**

Run:

```bash
python3 -m pytest tools/tests/test_provider_contract.py -q
```

Expected: 因 `SnapshotEnvelope` / `SnapshotPlan` 未定义而失败。

**Step 3: 最小实现**

在 `tools/providers/base.py` 定义：

```python
@dataclass(frozen=True)
class BknContext:
    conversation_id: str
    interaction_id: str

@dataclass(frozen=True)
class SnapshotPlan:
    products: tuple[str, ...] = ()
    forecast_ids: tuple[str, ...] = ()
    material_codes: tuple[str, ...] = ()
    datasets: frozenset[str] = frozenset()

@dataclass(frozen=True)
class SnapshotEnvelope:
    snapshot: Snapshot
    snapshot_id: str
    captured_at: str
    knowledge_network_id: str
    source: Literal["openbkn", "offline_test"]
    conversation_id: str | None
    interaction_id: str | None
    resource_receipts: tuple[dict, ...]
    loaded_datasets: frozenset[str]

class SnapshotProvider(Protocol):
    def capture(
        self,
        plan: SnapshotPlan,
        *,
        bkn_context: BknContext | None,
    ) -> SnapshotEnvelope: ...
```

将 `tools/fn/snapshot.py` 的索引构建提取为 `build_snapshot(rows_by_dataset)`，CSV 加载复用该函数。

**Step 4: 运行测试**

```bash
python3 -m pytest tools/tests/test_provider_contract.py tools/tests/test_fn_core.py -q
```

Expected: PASS。

### Task 2: 接入官方 MCP Client Session

**Files:**
- Create: `tools/providers/mcp_session.py`
- Create: `tools/tests/test_mcp_session.py`
- Modify: `tools/requirements.txt`
- Modify: `tools/config.example.yaml`

**Step 1: 添加显式依赖**

使用包管理器添加官方 MCP Python SDK 的当前最新版，不要手写猜测版本。

**Step 2: 写失败测试**

通过官方 MCP SDK 的测试 transport / fake `ClientSession` 验证：

- 使用官方 Streamable HTTP transport 连接 `<base-url>/api/agent-retrieval/v1/mcp`；
- transport 配置携带 `Authorization` 和 `x-business-domain`；
- 初始化后先读取 `tools/list`，服务端 Schema 是唯一权威来源；
- 调用只使用官方 `ClientSession.call_tool`；
- 不实现自定义 JSON-RPC、HTTP 重试或 Context Loader API 类；
- Context Loader 原始错误和 `bkn_receipt` 原样交给 Provider；
- 不执行 CLI fallback。

示例：

```python
async def test_session_factory_returns_official_client_session(fake_transport):
    async with open_context_session(
        base_url="http://localhost",
        app_key="bak_test",
        business_domain="bd_public",
        transport_factory=fake_transport,
    ) as session:
        assert isinstance(session, ClientSession)
```

**Step 3: 运行失败测试**

```bash
python3 -m pytest tools/tests/test_mcp_session.py -q
```

**Step 4: 实现最小 Session Factory**

要求：

- 只负责创建和关闭官方 `ClientSession`；
- 只负责配置 endpoint、认证 header、业务域和超时；
- 不暴露自定义 `call_tool` 包装；
- 不复制工具 Schema；
- 不自行管理 `bkn_start_interaction` / `bkn_finish_interaction`；
- 不记录 AppKey；
- 不自行重试业务调用；
- 第三方 Agent 或验收工具负责受管 Interaction 生命周期。

**Step 5: 运行测试**

```bash
python3 -m pytest tools/tests/test_mcp_session.py -q
```

Expected: PASS。

### Task 3: 实现 OpenBKNContextProvider

**Files:**
- Create: `tools/providers/openbkn_context_provider.py`
- Create: `tools/providers/resource_contract.py`
- Create: `tools/tests/test_openbkn_context_provider.py`
- Create: `tools/tests/fixtures/context_loader_responses/`

**Step 1: 写资源合同**

为下列逻辑数据集定义必要字段：

- `product`
- `forecast`
- `bom`
- `material`
- `inventory`
- `purchase_order`
- `purchase_request`
- `mrp`
- `production_plan`

每个合同包含：

- BKN 对象类型 ID；
- 资源绑定名称；
- 逻辑字段；
- 可接受物理字段别名；
- 必填字段；
- 查询过滤字段。

**Step 2: 写失败测试**

覆盖：

- Schema 和 Resource ID 可发现；
- Schema/Resource 元数据可缓存；
- 业务数据不缓存；
- 先查 BOM，再按相关物料裁剪库存和单据；
- `run_sql` 使用真实 resource ID 占位符；
- MySQL 标识符使用反引号；
- 缺必填字段返回 `schema_mismatch`；
- 查询结果组装为 `SnapshotEnvelope`；
- Provider 不读取 CSV。

**Step 3: 实现 Provider**

核心接口：

```python
class OpenBKNContextProvider:
    def capture(
        self,
        plan: SnapshotPlan,
        *,
        bkn_context: BknContext | None,
    ) -> SnapshotEnvelope:
        ...
```

实现顺序：

1. 校验 `bkn_context`；
2. 接收已初始化的官方 `ClientSession`；
3. 通过 `ClientSession.call_tool` 发现或读取缓存的资源合同；
4. 查询产品/预测；
5. 查询 BOM；
6. 提取物料编码；
7. 分批查询库存、PO、PR、MRP 和物料主数据；
8. 构建 Snapshot；
9. 返回所有 receipt。

IN 条件必须分批，单批数量由配置控制。
Provider 只做业务查询编排和 Snapshot 映射，不得出现自定义 HTTP、JSON-RPC 或 Context Loader 客户端实现。

**Step 4: 运行测试**

```bash
python3 -m pytest tools/tests/test_openbkn_context_provider.py -q
```

Expected: PASS。

### Task 4: FastAPI Provider 注入与 readiness

**Files:**
- Modify: `tools/fn_service.py`
- Create: `tools/service_dependencies.py`
- Create: `tools/tests/test_fn_service_runtime.py`
- Modify: `tools/tests/test_fn_service.py`

**Step 1: 写失败测试**

覆盖：

- 模块导入时不加载 CSV；
- 默认运行时 Provider 是 OpenBKN；
- `/health` 不访问远端；
- `/ready` 校验认证、KN、Resource 合同和 Context Loader；
- `/ready` 不进入 OpenAPI；
- Tool 响应包含 `snapshot_meta`；
- OpenBKN 失败时返回 503；
- 不降级 CSV；
- 测试可注入 `CsvSnapshotProvider`。

**Step 2: 删除全局快照**

移除：

```python
SNAPSHOT = load_csv_snapshot()
```

替换为 FastAPI dependency：

```python
def get_snapshot_provider() -> SnapshotProvider:
    return runtime_provider
```

每个 endpoint 根据输入构造 `SnapshotPlan` 后获取 `SnapshotEnvelope`。

**Step 3: 新增上下文请求模型**

```python
class BknContextRequest(BaseModel):
    conversation_id: str
    interaction_id: str
```

所有业务请求增加：

```python
bkn_context: BknContextRequest | None
```

生产模式缺少上下文时返回 `context_required`。

**Step 4: 运行服务测试**

```bash
python3 -m pytest tools/tests/test_fn_service.py tools/tests/test_fn_service_runtime.py -q
```

Expected: PASS。

### Task 5: 新增安全未关闭预测 Tool

**Files:**
- Create: `tools/fn/forecast.py`
- Modify: `tools/fn/__init__.py`
- Modify: `tools/fn_service.py`
- Modify: `tools/export_fn_openapi.py`
- Create: `tools/tests/test_forecast.py`

**Step 1: 写失败测试**

覆盖：

- 默认排除 `closestatus_title == 已关闭`；
- 可按产品编码追加过滤；
- API 不暴露 `include_closed`；
- 全网和单产品结果与独立 Snapshot 计算一致；
- 缺 Context 时运行模式拒绝。

**Step 2: 实现**

纯函数：

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

**Step 3: 运行测试并导出 OpenAPI**

```bash
python3 -m pytest tools/tests/test_forecast.py tools/tests/test_fn_service.py -q
python3 tools/export_fn_openapi.py
```

Expected:

- 测试通过；
- OpenAPI 3.0.3；
- 12 个业务 Tool；
- 无 `type: null`。

## Gate A：只读运行时确认

展示：

- 本地 diff；
- 新增测试数和结果；
- `/ready` 输出；
- OpenBKN 实时查询证据；
- 无 CSV fallback 证明；
- 12 Tool OpenAPI diff。

取得确认后进入阶段 B。不得在此门禁前上传 Toolbox。

## 阶段 B：S1 综合倒排与 Skill

### Task 6: 为 S1 倒排建立测试向量

**Files:**
- Create: `tools/tests/test_backward_plan.py`
- Create: `tools/tests/fixtures/backward_plan/`

**Step 1: 写日期树测试**

至少覆盖：

- L0 起止；
- 子件 `end=parent.start-1`；
- 外购/委外采购 LT；
- 自制生产 LT；
- LT 缺失按 0、条长至少 1；
- BOM 环路跳过；
- 5000 节点上限；
- 同料号最大延迟；
- A 类；
- B 类；
- 11 个供应状态；
- 无日期拒绝；
- 替代未确认拒绝；
- BOM 空拒绝。

测试预期必须来自规则公式和最小合成夹具，不读取业务问答测试集答案。

**Step 2: 运行失败测试**

```bash
python3 -m pytest tools/tests/test_backward_plan.py -q
```

Expected: `backward_plan` 不存在。

### Task 7: 实现 backward_plan 纯函数

**Files:**
- Create: `tools/fn/backward_plan.py`
- Modify: `tools/fn/__init__.py`
- Modify: `tools/fn/bom.py`
- Modify: `tools/fn/supply_status.py`

**Step 1: 定义输出模型**

```python
{
  "product_code": "...",
  "forecast_id": "...",
  "demand_qty": 0,
  "demand_end": "YYYY-MM-DD",
  "warehouse_scope": [],
  "substitute_enabled": False,
  "can_deliver_on_time": False,
  "max_delay_days": 0,
  "delay_a": [],
  "delay_b": [],
  "nodes": [],
  "gaps": [],
  "warnings": []
}
```

每个 node 必须包含：

- material code；
- parent；
- level；
- usage；
- gross requirement；
- start/end；
- lead time；
- available/in-transit；
- supply status；
- delay class；
- evidence。

**Step 2: 最小实现**

复用：

- `children_by_parent`
- `available_qty`
- `in_transit_qty`
- `leadtime_days`
- `supply_status`

禁止复制这些公式。

**Step 3: 运行测试**

```bash
python3 -m pytest tools/tests/test_backward_plan.py tools/tests/test_fn_core.py -q
```

Expected: PASS。

### Task 8: 暴露 backward_plan Tool

**Files:**
- Modify: `tools/fn_service.py`
- Modify: `tools/export_fn_openapi.py`
- Modify: `tools/tests/test_fn_service.py`
- Modify: `tools/fn_cli.py`

**Step 1: 写失败 API 测试**

覆盖：

- 必须提供产品、forecast ID、日期和替代策略；
- 响应有 Snapshot/Trace；
- 无 BOM 返回结构化 422；
- summary/full_tree；
- OpenAPI operation ID 唯一。

**Step 2: 实现 API 和离线 CLI**

Tool：

- operation ID: `backward_plan`
- summary: `生产计划齐套倒排`

CLI 仅用于离线金标：

```bash
python3 tools/fn_cli.py backward-plan \
  --product 382-000005 \
  --forecast-id <id> \
  --demand-end 2026-05-14 \
  --qty 50 \
  --substitute no
```

**Step 3: 回归**

```bash
python3 -m pytest tools/tests -q
python3 tools/export_fn_openapi.py
```

Expected: 全部通过，OpenAPI 有 13 个业务 Tool。

### Task 9: 更新 S1/S2/S3 包

**Files:**
- Modify: `skills/production-schedule-backward-planning/SKILL.md`
- Modify: `skills/production-schedule-backward-planning/references/io-contract.md`
- Modify: `skills/production-schedule-backward-planning/references/business-rules.md`
- Modify: `skills/production-schedule-backward-planning/references/report-spec.md`
- Modify: `skills/production-schedule-backward-planning/references/kn-metrics.md`
- Modify: `skills/demand-fulfillment-capacity-analysis/SKILL.md`
- Modify: `skills/demand-fulfillment-requirement-coverage-analysis/SKILL.md`
- Create: `tools/tests/test_skill_contracts.py`

**Step 1: 写契约测试**

验证：

- S1 必须引用 `生产计划齐套倒排`；
- S1 不要求 Agent 重写公式；
- “未关闭预测单数”路由到安全 Tool；
- S2 不加在途；
- S3 在途只计未关闭 PO；
- 三个 Skill 都只建议 PR 决策，不创建 ERP PR/PO；
- 监控目标明确为产品 + 单张预测单；
- Action 必须人工确认。

**Step 2: 更新包内容**

版本号按语义版本递增 minor。

**Step 3: 运行契约测试**

```bash
python3 -m pytest tools/tests/test_skill_contracts.py -q
```

Expected: PASS。

### Task 10: 第三方只读验收工具

**Files:**
- Create: `tools/verify_partner_kit.py`
- Create: `tools/tests/test_verify_partner_kit.py`
- Create: `docs/第三方验收说明.md`

**Step 1: 写失败测试**

验证：

- `env` 检查 OpenBKN、KN、Context Loader、Toolbox 和 Skill；
- `integration` 只接受 `source=openbkn`；
- `blind-eval --questions-only` 只解析题号、场景和业务问题；
- 解析器禁止读取“参考答案”单元格；
- 输出 JSON 报告和证据路径；
- 凭据不进入报告。

**Step 2: 实现命令**

```bash
python3 tools/verify_partner_kit.py env
python3 tools/verify_partner_kit.py integration --kn-id supply_ontology_hand
python3 tools/verify_partner_kit.py blind-eval \
  --testset docs/业务问答测试集.md \
  --questions-only
```

**Step 3: 运行测试**

```bash
python3 -m pytest tools/tests/test_verify_partner_kit.py -q
```

Expected: PASS。

## Gate B：函数和 Skill 确认

展示：

- `backward_plan` 输入输出；
- S1 日期树、A/B、状态测试；
- 13 Tool OpenAPI；
- 三个 Skill diff；
- 第三方验收工具演示；
- 尚未发布到 localhost 的证明。

取得确认后进入阶段 C。

## 阶段 C：Dataset 与 BKN 模型

### Task 11: 编写三张结构化表 DDL

**Files:**
- Create: `datasets/postgres/001_action_datasets.sql`
- Create: `datasets/mysql/001_action_datasets.sql`
- Create: `datasets/README_cn.md`
- Create: `tools/tests/test_action_dataset_ddl.py`

**Step 1: 写 DDL 静态测试**

验证三张表存在：

- `sc_pr_decision`
- `sc_plan_monitor_task`
- `sc_plan_monitor_item`

验证：

- 主键；
- 外键或逻辑关联字段；
- 同一 forecast 仅一个未关闭任务的约束；
- 幂等键唯一；
- 状态 check/enum；
- 时间戳；
- MySQL/PostgreSQL 等价字段；
- 不含 ERP PR/PO 写入字段。

**Step 2: 编写 DDL**

按设计文档字段逐项实现。

**Step 3: SQLite/容器语法验证**

对可静态验证部分运行 pytest；如本机有 MySQL/PostgreSQL 测试容器，运行临时库 migration，不操作样例数据库。

### Task 12: Dataset 初始化、扫描与绑定脚本

**Files:**
- Create: `tools/setup_action_datasets.py`
- Create: `tools/bind_action_datasets.py`
- Create: `tools/tests/test_setup_action_datasets.py`
- Create: `tools/tests/test_bind_action_datasets.py`
- Modify: `tools/config.example.yaml`

**Step 1: 写 dry-run 测试**

验证：

- 默认 `--dry-run` 不执行 DDL；
- 输出将创建的表、Vega Resource、对象和关系；
- 重复运行幂等；
- 已存在但结构不一致时阻断；
- 密码不打印；
- `--apply` 必须显式传入。

**Step 2: 实现**

脚本职责：

1. 创建表；
2. 触发 Vega 扫描；
3. 等待 Resource 可用；
4. 输出 Resource ID；
5. 绑定对象；
6. 回读验证。

### Task 13: BKN 对象与关系变更载荷

**Files:**
- Create: `docs/payloads/action-dataset-object-types.json`
- Create: `docs/payloads/action-dataset-relation-types.json`
- Create: `tools/tests/test_action_bkn_payloads.py`
- Modify: `kn/supply_ontology_hand.json`

**Step 1: 写载荷测试**

对象：

- 新增采购申请决策；
- 绑定现有监控任务；
- 新增监控证据明细。

关系：

1. 监控任务 → 监控 → 产品
2. 监控任务 → 依据 → 需求预测
3. 监控任务 → 包含证据 → 监控证据明细
4. 监控证据明细 → 引用 → 物料
5. 采购申请决策 → 针对 → 产品
6. 采购申请决策 → 来源于 → 需求预测
7. 采购申请决策 → 建议采购 → 物料

验证 source/target、映射字段、显示键和主键。

**Step 2: 生成本地载荷**

不得调用 localhost create/update。

**Step 3: 静态校验**

```bash
python3 -m pytest tools/tests/test_action_bkn_payloads.py -q
```

Expected: PASS。

## Gate C：Dataset/BKN 变更确认

展示：

- 两套 DDL；
- 三张表字段；
- 对象/关系载荷；
- dry-run 输出；
- 回滚与数据保留方案。

用户确认后才允许 `--apply` 和 localhost BKN 更新。

## 阶段 D：Action 与监控

### Task 14: 批准凭证与幂等存储

**Files:**
- Create: `tools/action_gateway.py`
- Create: `tools/approval.py`
- Create: `tools/tests/test_approval.py`
- Create: `tools/tests/test_action_gateway.py`

**Step 1: 写安全失败测试**

覆盖：

- 无 token；
- 签名错误；
- proposal hash 不匹配；
- Interaction 不匹配；
- Action 类型不匹配；
- 过期；
- 幂等键重放；
- 管理员凭据缺失；
- Agent 请求不能签发 token。

**Step 2: 实现提案规范化**

JSON canonicalization 后计算 SHA-256。

批准 token 至少绑定：

- proposal hash；
- action type；
- interaction ID；
- approver；
- expiry；
- idempotency key。

**Step 3: 实现验证**

使用 `hmac.compare_digest`；批准 secret 只从环境变量读取。

**Step 4: 测试**

```bash
python3 -m pytest tools/tests/test_approval.py tools/tests/test_action_gateway.py -q
```

Expected: PASS。

### Task 15: 创建采购申请决策 Action

**Files:**
- Create: `tools/actions/pr_decision.py`
- Create: `tools/tests/test_pr_decision_action.py`
- Create: `docs/payloads/create-pr-decision-action.json`

**Step 1: 写失败测试**

验证：

- 只接收已批准提案；
- 每个物料一行；
- 同批使用相同 `decision_batch_id`；
- 保存 forecast/product/material/snapshot/interaction；
- 不调用 ERP；
- 重放不重复插入；
- 可经 OpenBKN Resource 回读。

**Step 2: 实现事务写入**

Action Gateway 是三张专用表唯一写入口。

**Step 3: dry-run**

使用临时测试库，不写 localhost Dataset。

### Task 16: 创建与关闭监控任务 Action

**Files:**
- Create: `tools/actions/monitor_task.py`
- Create: `tools/tests/test_monitor_task_action.py`
- Create: `docs/payloads/create-monitor-task-action.json`
- Create: `docs/payloads/close-monitor-task-action.json`

**Step 1: 写失败测试**

验证：

- 一任务只对应一个产品和一张预测单；
- 同 forecast 不重复创建未关闭任务；
- 创建前执行 S1；
- 主表与明细事务一致；
- 明细物料只是证据；
- 关闭保留明细；
- 创建和关闭都需要批准；
- 预测关闭不自动删除。

**Step 2: 实现**

创建结果返回：

- task ID；
- 首次 S1 摘要；
- 写入行数；
- snapshot；
- Trace。

### Task 17: 实现 monitor_runner

**Files:**
- Create: `tools/monitor_runner.py`
- Create: `tools/tests/test_monitor_runner.py`
- Create: `docs/监控任务运行说明.md`

**Step 1: 写失败测试**

验证：

- 只通过 OpenBKN 查询打开任务；
- 每任务重建实时 Snapshot；
- 更新主表和证据明细；
- 预测数量/截止日变化更新基线；
- 风险变化可追溯；
- 预测关闭只标记待关闭；
- 单任务失败不阻断其他任务；
- 并发租约避免重复刷新。

**Step 2: 实现单次运行模式**

```bash
python3 tools/monitor_runner.py run-once --dry-run
```

先只实现 `run-once`；持续调度交给部署环境，避免自建常驻调度框架。

**Step 3: 测试**

```bash
python3 -m pytest tools/tests/test_monitor_runner.py -q
```

Expected: PASS。

## Gate D：Action 本地验收确认

展示：

- Action 请求/响应；
- 批准、过期、重放测试；
- 临时库写入和回读；
- monitor runner dry-run；
- 没有 ERP 调用的证明。

确认后才进入 localhost 注册。

## 阶段 E：localhost 平台更新

### Task 18: 生成平台变更清单

**Files:**
- Create: `docs/localhost-P0变更清单.md`
- Create: `tools/build_platform_change_manifest.py`

清单必须列出：

- metric ID、旧名、新名；
- 13 个 Tool 的 ID、新增/更新状态；
- Skill ID、旧版本、新版本；
- 三个 Dataset Resource；
- 对象和关系；
- Action 新增/修改；
- 原 PO Action 降级；
- 索引重建；
- 回滚步骤。

不得在生成清单时执行写操作。

### Task 19: 经确认后应用 Dataset 和 BKN 变更

**Precondition:** 用户对 `docs/localhost-P0变更清单.md` 明确确认。

执行顺序：

1. 创建三张表；
2. Vega 扫描；
3. 创建/绑定对象；
4. 创建关系；
5. 回读验证；
6. 失败则停止，不继续 Action 注册。

每一步保存 JSON 回执。

### Task 20: 经确认后更新指标、Toolbox 和 Skill

**Precondition:** Task 19 通过。

执行顺序：

1. 更新预测计数 metric 显示名和注释；
2. 上传 13 Tool OpenAPI；
3. 逐个启用并 smoke test；
4. 更新三个 Skill 包；
5. 发布；
6. 重建 Context Loader 索引；
7. 验证 `find_skills` 3/3。

### Task 21: 经确认后注册 Action

**Precondition:** Action Gateway `/ready` 通过。

执行顺序：

1. 注册 `create_pr_decision`；
2. 更新 `create_monitor_task`；
3. 注册 `close_monitor_task`；
4. 从第三方 Agent 可调用说明中移除原 PO Action；
5. 仅执行 dry-run；
6. 不创建真实业务记录。

## 阶段 F：第三方验收

### Task 22: 全量自动化测试

Run:

```bash
python3 -m pytest tools/tests -q
```

Expected: 0 failed。

### Task 23: 第三方环境和集成验收

Run:

```bash
python3 tools/verify_partner_kit.py env
python3 tools/verify_partner_kit.py integration \
  --kn-id supply_ontology_hand
python3 tools/verify_partner_kit.py actions --dry-run
```

Expected:

- 所有检查通过；
- Tool 响应 `source=openbkn`；
- Action 绕过全部拒绝；
- 无 ERP 调用。

### Task 24: 178 题盲测

Run:

```bash
python3 tools/verify_partner_kit.py blind-eval \
  --testset docs/业务问答测试集.md \
  --questions-only
```

要求：

- 只读取题号、场景、业务问题；
- 保存每题路由、结果、Snapshot 和 Trace；
- 不读取参考答案；
- 用独立 OpenBKN 查询或离线公式交叉核验；
- 更新验证 Canvas。

### Task 25: 第三方交付文档

**Files:**
- Create: `docs/第三方安装说明.md`
- Modify: `docs/第三方验收说明.md`
- Modify: `docs/动力层建设方案.md`
- Modify: `docs/动力层落地说明书.md`
- Modify: `README_cn.md`
- Modify: `README.md`

文档必须覆盖：

- 安装；
- AppKey 和业务域；
- Dataset 初始化；
- Toolbox/Skill/Action 注册；
- 监控 runner；
- 验收；
- 错误码；
- 安全；
- 卸载；
- 数据保留；
- 平台版本差异。

不得包含开发过程叙事或内部临时路径。

## 最终放行检查

- [ ] 运行时无 CSV fallback
- [ ] `/ready` 通过
- [ ] 13 个 Tool 可调用
- [ ] S1 核心场景可执行
- [ ] S1/S2/S3 召回 3/3
- [ ] 未关闭预测安全过滤
- [ ] PR 决策可写可读
- [ ] 产品 + 单预测单监控可写可读可刷新
- [ ] 无授权/伪造/过期/重放全部拒绝
- [ ] 不调用 ERP PR/PO
- [ ] 全量 pytest 0 failed
- [ ] 178 题盲测完成
- [ ] 第三方文档完整
- [ ] 平台回执归档

## 实施交接

推荐按阶段执行，每个 Gate 停下来评审：

1. Gate A：OpenBKN-only 只读运行时；
2. Gate B：S1 与 Skill；
3. Gate C：Dataset 与 BKN 模型；
4. Gate D：Action 本地 dry-run；
5. localhost 平台变更确认；
6. 第三方全量验收。

开始实施前，先确认是否进入阶段 A。未经确认，不执行任何任务。

