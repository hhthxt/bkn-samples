# Action Dataset 结构化表说明

> 知识网络：`供应链本体知识网络-手工版`（`supply_ontology_hand`）
> 依据：`docs/第三方可验证动力层P0优化设计.md` 9.1-9.4
> 适用阶段：阶段 C（Dataset 与 BKN 模型）

## 1. 表清单

| 表名 | 用途 | 对应对象 |
|---|---|---|
| `sc_pr_decision` | 采购申请决策记录（人工批准后的采购建议） | `supply_ontology_hand_pr_decision` |
| `sc_plan_monitor_task` | 生产计划倒排监控任务（一个产品 + 一张需求预测） | 现有监控任务对象 |
| `sc_plan_monitor_item` | 监控证据明细（任务对应的 BOM 供应证据） | `supply_ontology_hand_mon_item` |

三张表都是决策与监控记录表：**本期不调用 ERP**，不写入、不同步、不引用 ERP 采购申请或采购订单单据号；`sc_pr_decision` 是决策记录，不是 ERP 采购申请。

## 1.1 Skill Registry (Agent recall prerequisite)

`public.skills` is the Context Loader registry used by `find_skills`; it does not replace OpenBKN Skill API registration. Agent mode must run: register/publish Skills through the API → `tools/setup_skill_dataset.py --interactive --apply` to create and seed the table from the current environment → Catalog Discover → `tools/bind_skill_dataset.py --apply` to bind object class ID `skills` to the discovered Resource. API registration alone, with a null `data_source` on `skills`, makes `find_skills` fail.

PostgreSQL DDL: `datasets/postgres/002_skill_registry.sql`. The table stores Skill discovery metadata only; it stores no credentials or Skill file bodies.

## 2. 安装

脚本按方言分目录，文件名一致：

- PostgreSQL：`datasets/postgres/001_action_datasets.sql`（建议 12+）
- MySQL 8.0.16+：`datasets/mysql/001_action_datasets.sql`

### 2.0 最低版本与 CHECK 生效前提

MySQL 最低版本是 **MySQL 8.0.16+**，原因是本脚本用 CHECK 约束承载状态枚举与审批审计规则：

- MySQL 8.0.16 起 CHECK 约束才被真正强制执行；
- 8.0.16 之前的版本会解析并忽略 CHECK 约束，状态枚举、审批审计、数量非负都将失去数据库层保护；
- 因此在 8.0.16 之前的版本上安装等同于放弃约束，Action 网关必须自行兜底校验，不建议用于验收；
- 生成列 `active_forecast_id` 与其唯一约束需要 MySQL 5.7+，不构成额外限制。

PostgreSQL 侧 CHECK 一直生效，无额外版本前提。

安装步骤：

1. 准备一个独立库或独立 schema，不要与样例业务库混用；
2. 使用只对该库有 DDL 权限的账号；
3. 执行对应方言的 `001_action_datasets.sql`；
4. 通过 Vega 扫描为 Resource，并绑定 BKN 对象。默认 dry-run：

```bash
python3 tools/setup_action_datasets.py --config tools/config.yaml
python3 tools/bind_action_datasets.py --config tools/config.yaml
```

只有显式传入 `--apply` 才会执行 DDL 或更新平台对象。

PostgreSQL：

```bash
psql "$PG_DSN" -v ON_ERROR_STOP=1 -f datasets/postgres/001_action_datasets.sql
```

MySQL：

```bash
mysql --host "$MYSQL_HOST" --user "$MYSQL_USER" -p "$MYSQL_DB" < datasets/mysql/001_action_datasets.sql
```

两套脚本幂等：均使用 `CREATE TABLE IF NOT EXISTS` 与 `CREATE INDEX IF NOT EXISTS`（MySQL 索引内联在建表语句中），重复执行不会破坏已有数据。

### 2.1 两套方言的等价性

字段集合完全一致，仅数据类型按方言映射：

| 语义 | PostgreSQL | MySQL |
|---|---|---|
| 时间戳 | `TIMESTAMPTZ` | `DATETIME(6)` |
| 布尔 | `BOOLEAN` | `BOOLEAN`（`TINYINT(1)`） |
| 数量 | `DECIMAL(18,4)` | `DECIMAL(18,4)` |
| 字符集 | 库级 UTF-8 | 表级 `utf8mb4` |

`sc_plan_monitor_item.updated_at` 的自动刷新在两套方言里实现方式不同，语义等价：

- MySQL：列上声明 `ON UPDATE CURRENT_TIMESTAMP(6)`；
- PostgreSQL：`sc_set_updated_at()` 触发器函数 + `trg_sc_plan_monitor_item_updated_at` BEFORE UPDATE trigger 逐行刷新。

因此两侧都不需要应用层显式写 `updated_at`；若刷新脚本显式传入该字段，PostgreSQL trigger 仍会覆盖为当前时间。

“同一 `forecast_id` 只允许一个未关闭任务”的实现方式不同，但语义等价：

- PostgreSQL：`uk_sc_plan_monitor_task_open_forecast` 部分唯一索引，条件为 `task_status NOT IN ('completed','closed')`；
- MySQL：生成列 `active_forecast_id`（关闭态取 `NULL`）+ 唯一约束。

`active_forecast_id` 是 MySQL 唯一的辅助列，不参与业务读写，Vega 扫描后不需要绑定到对象属性。

## 3. 默认 dry-run 边界

阶段 C 与阶段 D 的写入链路默认 dry-run：

- 初始化与绑定脚本默认 `--dry-run`，只打印将要执行的 DDL 与绑定请求，不连接数据库执行、不修改平台对象；
- 只有显式传入 `--apply`（或 `--no-dry-run`）并提供目标连接串时才真正执行；
- Action 写入（`create_pr_decision` / `create_monitor_task` / `close_monitor_task`）在 dry-run 下只校验批准凭证、幂等键和快照，不落库；
- dry-run 与真实执行都不会调用 ERP，也不会向 ERP 发起任何采购动作；
- 单元测试只做静态 DDL 文本校验，不需要数据库，不执行 DDL。

## 4. 数据保留

- 决策与监控数据为审计证据，默认永久保留，不做自动清理；
- 状态流转不删除历史行：决策取消写 `status='cancelled'`，任务结束写 `task_status='closed'` 与 `closed_at`；
- 审批审计约束 `ck_sc_pr_decision_approval_audit` 要求 `status='approved'` 时 `approved_by` 与 `approved_at` 都非空；`rejected` / `cancelled` 不强制清空这两个字段，便于保留曾审批与处置证据；
- `monitor_runner` 刷新只更新任务主表与证据明细的当前值，不追加或删除任务行；
- 预测单关闭时提示人工关闭任务，不自动删除任务或证据明细；
- 需要清理时，先归档导出再删除，且必须保留 `snapshot_id` 与 `interaction_id` 以维持 Trace 可追溯；
- 证据明细随任务级联删除（`ON DELETE CASCADE`），因此删除任务前必须确认已完成归档。

## 5. 备份建议

- 变更前对目标库做一次完整备份：PostgreSQL 用 `pg_dump`，MySQL 用 `mysqldump --single-transaction`；
- 三张表体积小，建议每日逻辑备份并保留 30 天；
- 执行任何删表操作前，单独导出三张表的数据快照，并校验导出行数；
- 备份文件与平台绑定配置一同保存，便于重新扫描与绑定后恢复。

## 6. 卸载顺序

删除必须按外键依赖自下而上执行，先删除证据明细，再删除任务主表，最后删除决策表：

```sql
DROP TABLE IF EXISTS sc_plan_monitor_item;
DROP TABLE IF EXISTS sc_plan_monitor_task;
DROP TABLE IF EXISTS sc_pr_decision;
```

PostgreSQL 额外一步（表删除后再删刷新函数，trigger 随表自动删除）：

```sql
DROP FUNCTION IF EXISTS sc_set_updated_at();
```

顺序说明：

1. `sc_plan_monitor_item` 通过 `task_id` 外键依赖任务主表，必须先删除；
2. `sc_plan_monitor_task` 在证据明细删除后才能删除；
3. `sc_pr_decision` 无外键依赖，最后删除；
4. 删除前先在平台侧解绑对应 Resource 与 BKN 对象，避免留下悬空绑定；
5. 若只需下线能力而保留证据，建议只解绑 Resource 并保留三张表数据。
