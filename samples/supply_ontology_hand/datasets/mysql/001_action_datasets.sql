-- Action Dataset DDL (MySQL 8.0.16+)
-- 版本前提：CHECK 约束自 MySQL 8.0.16 起才被强制执行，8.0.16 之前只解析不生效。
-- 知识网络：supply_ontology_hand
-- 依据：docs/第三方可验证动力层P0优化设计.md 9.2 / 9.3 / 9.4
-- 说明：三张表只保存决策与监控记录，不保存任何 ERP 采购单据号，本期不调用 ERP。
-- 字段集合与 datasets/postgres/001_action_datasets.sql 等价，仅多一个未关闭唯一性辅助生成列。

-- 9.2 采购申请决策：决策记录，不是 ERP 采购申请
CREATE TABLE IF NOT EXISTS sc_pr_decision (
    decision_id VARCHAR(64) NOT NULL COMMENT '决策行主键',
    decision_batch_id VARCHAR(64) NOT NULL COMMENT '同批物料建议分组',
    forecast_id VARCHAR(64) NOT NULL COMMENT '来源需求预测',
    product_code VARCHAR(64) NOT NULL COMMENT '来源产品',
    material_code VARCHAR(64) NOT NULL COMMENT '建议采购物料',
    recommended_qty DECIMAL(18, 4) NOT NULL DEFAULT 0 COMMENT '建议数量',
    required_date DATE NULL COMMENT '要求到位日',
    warehouse_scope VARCHAR(64) NOT NULL DEFAULT 'ALL' COMMENT '仓范围',
    substitute_enabled BOOLEAN NOT NULL DEFAULT FALSE COMMENT '替代策略',
    reason_code VARCHAR(64) NOT NULL DEFAULT 'shortage' COMMENT '缺口原因',
    snapshot_id VARCHAR(64) NOT NULL COMMENT '计算快照',
    interaction_id VARCHAR(64) NOT NULL COMMENT 'OpenBKN Interaction',
    status VARCHAR(16) NOT NULL COMMENT 'approved / rejected / cancelled',
    approved_by VARCHAR(64) NULL COMMENT '批准人',
    approved_at DATETIME(6) NULL COMMENT '批准时间',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
    idempotency_key VARCHAR(128) NOT NULL COMMENT '批准凭证幂等键',
    PRIMARY KEY (decision_id),
    CONSTRAINT uk_sc_pr_decision_idempotency UNIQUE (idempotency_key),
    CONSTRAINT ck_sc_pr_decision_status CHECK (status IN ('approved', 'rejected', 'cancelled')),
    CONSTRAINT ck_sc_pr_decision_qty CHECK (recommended_qty >= 0),
    -- 审批审计：approved 必须留下批准人与批准时间；rejected / cancelled 允许保留曾审批证据
    CONSTRAINT ck_sc_pr_decision_approval_audit CHECK (
        status <> 'approved' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)
    ),
    KEY idx_sc_pr_decision_forecast (forecast_id, status),
    KEY idx_sc_pr_decision_product (product_code, status),
    KEY idx_sc_pr_decision_material (material_code, required_date),
    KEY idx_sc_pr_decision_batch (decision_batch_id),
    KEY idx_sc_pr_decision_snapshot (snapshot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='采购申请决策记录，不含 ERP 单据号';

-- 9.3 生产计划倒排监控任务：一个产品 + 一张需求预测
CREATE TABLE IF NOT EXISTS sc_plan_monitor_task (
    task_id VARCHAR(64) NOT NULL COMMENT '任务主键',
    product_code VARCHAR(64) NOT NULL COMMENT '被监控产品',
    forecast_id VARCHAR(64) NOT NULL COMMENT '被监控需求预测',
    forecast_qty DECIMAL(18, 4) NOT NULL DEFAULT 0 COMMENT '预测数量基线',
    demand_end DATE NULL COMMENT '需求截止日基线',
    warehouse_scope VARCHAR(64) NOT NULL DEFAULT 'ALL' COMMENT '仓范围',
    substitute_enabled BOOLEAN NOT NULL DEFAULT FALSE COMMENT '替代策略',
    kitting_status VARCHAR(32) NOT NULL DEFAULT 'unknown' COMMENT '当前齐套状态',
    can_deliver_on_time BOOLEAN NULL COMMENT '当前是否可按期',
    max_delay_days INT NULL COMMENT '当前最大延迟天数',
    planned_start DATE NULL COMMENT '倒排生产开始日',
    planned_end DATE NULL COMMENT '需求截止日',
    snapshot_id VARCHAR(64) NULL COMMENT '最近快照',
    task_status VARCHAR(16) NOT NULL DEFAULT 'watching' COMMENT 'watching / risk / ready / completed / closed',
    check_interval INT NOT NULL DEFAULT 1440 COMMENT '检查频率，单位分钟',
    next_check_at DATETIME(6) NULL COMMENT '下次检查时间',
    last_checked_at DATETIME(6) NULL COMMENT '最近检查时间',
    created_by VARCHAR(64) NOT NULL DEFAULT 'system' COMMENT '创建人',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
    closed_at DATETIME(6) NULL COMMENT '关闭时间',
    active_forecast_id VARCHAR(64) GENERATED ALWAYS AS (
        IF(task_status IN ('completed', 'closed'), NULL, forecast_id)
    ) STORED COMMENT '未关闭任务唯一性辅助列，等价于 PostgreSQL partial unique index',
    PRIMARY KEY (task_id),
    CONSTRAINT uk_sc_plan_monitor_task_open_forecast UNIQUE (active_forecast_id),
    CONSTRAINT ck_sc_plan_monitor_task_status CHECK (
        task_status IN ('watching', 'risk', 'ready', 'completed', 'closed')
    ),
    CONSTRAINT ck_sc_plan_monitor_task_interval CHECK (check_interval > 0),
    CONSTRAINT ck_sc_plan_monitor_task_delay CHECK (max_delay_days IS NULL OR max_delay_days >= 0),
    KEY idx_sc_plan_monitor_task_product (product_code, task_status),
    KEY idx_sc_plan_monitor_task_forecast (forecast_id, task_status),
    KEY idx_sc_plan_monitor_task_next_check (next_check_at, task_status),
    KEY idx_sc_plan_monitor_task_snapshot (snapshot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='生产计划倒排监控任务，产品加单张需求预测粒度';

-- 9.4 监控证据明细：BOM 供应证据，不是监控目标
CREATE TABLE IF NOT EXISTS sc_plan_monitor_item (
    item_id VARCHAR(64) NOT NULL COMMENT '明细主键',
    task_id VARCHAR(64) NOT NULL COMMENT '监控任务',
    material_code VARCHAR(64) NOT NULL COMMENT 'BOM 物料',
    bom_level INT NOT NULL DEFAULT 1 COMMENT 'BOM 层级',
    l1_parent VARCHAR(64) NULL COMMENT '一层父件',
    gross_requirement DECIMAL(18, 4) NOT NULL DEFAULT 0 COMMENT '毛需求',
    required_date DATE NULL COMMENT '要求到位日',
    available_qty DECIMAL(18, 4) NOT NULL DEFAULT 0 COMMENT '当前可用',
    in_transit_qty DECIMAL(18, 4) NOT NULL DEFAULT 0 COMMENT '当前在途',
    expected_arrival DATE NULL COMMENT '预计到货日',
    net_shortage DECIMAL(18, 4) NOT NULL DEFAULT 0 COMMENT '当前净缺口',
    delay_class VARCHAR(8) NOT NULL DEFAULT 'none' COMMENT 'A / B / none',
    supply_status VARCHAR(32) NOT NULL DEFAULT 'unknown' COMMENT '供应状态',
    snapshot_id VARCHAR(64) NULL COMMENT '最近快照',
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新时间',
    PRIMARY KEY (item_id),
    CONSTRAINT fk_sc_plan_monitor_item_task FOREIGN KEY (task_id) REFERENCES sc_plan_monitor_task (task_id) ON DELETE CASCADE,
    CONSTRAINT ck_sc_plan_monitor_item_delay_class CHECK (delay_class IN ('A', 'B', 'none')),
    CONSTRAINT ck_sc_plan_monitor_item_bom_level CHECK (bom_level >= 0),
    KEY idx_sc_plan_monitor_item_task (task_id, bom_level),
    KEY idx_sc_plan_monitor_item_material (material_code, required_date),
    KEY idx_sc_plan_monitor_item_status (supply_status, delay_class),
    KEY idx_sc_plan_monitor_item_snapshot (snapshot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='监控证据明细，任务对应的 BOM 物料供应证据';
