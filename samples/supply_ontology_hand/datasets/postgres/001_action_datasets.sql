-- Action Dataset DDL (PostgreSQL)
-- 知识网络：supply_ontology_hand
-- 依据：docs/第三方可验证动力层P0优化设计.md 9.2 / 9.3 / 9.4
-- 说明：三张表只保存决策与监控记录，不保存任何 ERP 采购单据号，本期不调用 ERP。

BEGIN;

-- 9.2 采购申请决策：决策记录，不是 ERP 采购申请
CREATE TABLE IF NOT EXISTS sc_pr_decision (
    decision_id VARCHAR(64) NOT NULL,
    decision_batch_id VARCHAR(64) NOT NULL,
    forecast_id VARCHAR(64) NOT NULL,
    product_code VARCHAR(64) NOT NULL,
    material_code VARCHAR(64) NOT NULL,
    recommended_qty DECIMAL(18, 4) NOT NULL DEFAULT 0,
    required_date DATE NULL,
    warehouse_scope VARCHAR(64) NOT NULL DEFAULT 'ALL',
    substitute_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    reason_code VARCHAR(64) NOT NULL DEFAULT 'shortage',
    snapshot_id VARCHAR(64) NOT NULL,
    interaction_id VARCHAR(64) NOT NULL,
    status VARCHAR(16) NOT NULL,
    approved_by VARCHAR(64) NULL,
    approved_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    idempotency_key VARCHAR(128) NOT NULL,
    CONSTRAINT pk_sc_pr_decision PRIMARY KEY (decision_id),
    CONSTRAINT uk_sc_pr_decision_idempotency UNIQUE (idempotency_key),
    CONSTRAINT ck_sc_pr_decision_status CHECK (status IN ('approved', 'rejected', 'cancelled')),
    CONSTRAINT ck_sc_pr_decision_qty CHECK (recommended_qty >= 0),
    -- 审批审计：approved 必须留下批准人与批准时间；rejected / cancelled 允许保留曾审批证据
    CONSTRAINT ck_sc_pr_decision_approval_audit CHECK (
        status <> 'approved' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_sc_pr_decision_forecast ON sc_pr_decision (forecast_id, status);
CREATE INDEX IF NOT EXISTS idx_sc_pr_decision_product ON sc_pr_decision (product_code, status);
CREATE INDEX IF NOT EXISTS idx_sc_pr_decision_material ON sc_pr_decision (material_code, required_date);
CREATE INDEX IF NOT EXISTS idx_sc_pr_decision_batch ON sc_pr_decision (decision_batch_id);
CREATE INDEX IF NOT EXISTS idx_sc_pr_decision_snapshot ON sc_pr_decision (snapshot_id);

COMMENT ON TABLE sc_pr_decision IS '采购申请决策记录：人工批准后的采购建议，不含 ERP 单据号';
COMMENT ON COLUMN sc_pr_decision.status IS 'approved / rejected / cancelled';
COMMENT ON COLUMN sc_pr_decision.idempotency_key IS '批准凭证幂等键，重放写入必须失败';

-- 9.3 生产计划倒排监控任务：一个产品 + 一张需求预测
CREATE TABLE IF NOT EXISTS sc_plan_monitor_task (
    task_id VARCHAR(64) NOT NULL,
    product_code VARCHAR(64) NOT NULL,
    forecast_id VARCHAR(64) NOT NULL,
    forecast_qty DECIMAL(18, 4) NOT NULL DEFAULT 0,
    demand_end DATE NULL,
    warehouse_scope VARCHAR(64) NOT NULL DEFAULT 'ALL',
    substitute_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    kitting_status VARCHAR(32) NOT NULL DEFAULT 'unknown',
    can_deliver_on_time BOOLEAN NULL,
    max_delay_days INTEGER NULL,
    planned_start DATE NULL,
    planned_end DATE NULL,
    snapshot_id VARCHAR(64) NULL,
    task_status VARCHAR(16) NOT NULL DEFAULT 'watching',
    check_interval INTEGER NOT NULL DEFAULT 1440,
    next_check_at TIMESTAMPTZ NULL,
    last_checked_at TIMESTAMPTZ NULL,
    created_by VARCHAR(64) NOT NULL DEFAULT 'system',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ NULL,
    CONSTRAINT pk_sc_plan_monitor_task PRIMARY KEY (task_id),
    CONSTRAINT ck_sc_plan_monitor_task_status CHECK (
        task_status IN ('watching', 'risk', 'ready', 'completed', 'closed')
    ),
    CONSTRAINT ck_sc_plan_monitor_task_interval CHECK (check_interval > 0),
    CONSTRAINT ck_sc_plan_monitor_task_delay CHECK (max_delay_days IS NULL OR max_delay_days >= 0)
);

-- 同一 forecast_id 只允许一个未关闭任务（completed / closed 之外的状态）
CREATE UNIQUE INDEX IF NOT EXISTS uk_sc_plan_monitor_task_open_forecast ON sc_plan_monitor_task (forecast_id) WHERE task_status NOT IN ('completed', 'closed');
CREATE INDEX IF NOT EXISTS idx_sc_plan_monitor_task_product ON sc_plan_monitor_task (product_code, task_status);
CREATE INDEX IF NOT EXISTS idx_sc_plan_monitor_task_forecast ON sc_plan_monitor_task (forecast_id, task_status);
CREATE INDEX IF NOT EXISTS idx_sc_plan_monitor_task_next_check ON sc_plan_monitor_task (next_check_at, task_status);
CREATE INDEX IF NOT EXISTS idx_sc_plan_monitor_task_snapshot ON sc_plan_monitor_task (snapshot_id);

COMMENT ON TABLE sc_plan_monitor_task IS '生产计划倒排监控任务：产品 + 单张需求预测粒度';
COMMENT ON COLUMN sc_plan_monitor_task.task_status IS 'watching / risk / ready / completed / closed';
COMMENT ON COLUMN sc_plan_monitor_task.check_interval IS '检查频率，单位分钟';

-- 9.4 监控证据明细：BOM 供应证据，不是监控目标
CREATE TABLE IF NOT EXISTS sc_plan_monitor_item (
    item_id VARCHAR(64) NOT NULL,
    task_id VARCHAR(64) NOT NULL,
    material_code VARCHAR(64) NOT NULL,
    bom_level INTEGER NOT NULL DEFAULT 1,
    l1_parent VARCHAR(64) NULL,
    gross_requirement DECIMAL(18, 4) NOT NULL DEFAULT 0,
    required_date DATE NULL,
    available_qty DECIMAL(18, 4) NOT NULL DEFAULT 0,
    in_transit_qty DECIMAL(18, 4) NOT NULL DEFAULT 0,
    expected_arrival DATE NULL,
    net_shortage DECIMAL(18, 4) NOT NULL DEFAULT 0,
    delay_class VARCHAR(8) NOT NULL DEFAULT 'none',
    supply_status VARCHAR(32) NOT NULL DEFAULT 'unknown',
    snapshot_id VARCHAR(64) NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_sc_plan_monitor_item PRIMARY KEY (item_id),
    CONSTRAINT fk_sc_plan_monitor_item_task FOREIGN KEY (task_id) REFERENCES sc_plan_monitor_task (task_id) ON DELETE CASCADE,
    CONSTRAINT ck_sc_plan_monitor_item_delay_class CHECK (delay_class IN ('A', 'B', 'none')),
    CONSTRAINT ck_sc_plan_monitor_item_bom_level CHECK (bom_level >= 0)
);

CREATE INDEX IF NOT EXISTS idx_sc_plan_monitor_item_task ON sc_plan_monitor_item (task_id, bom_level);
CREATE INDEX IF NOT EXISTS idx_sc_plan_monitor_item_material ON sc_plan_monitor_item (material_code, required_date);
CREATE INDEX IF NOT EXISTS idx_sc_plan_monitor_item_status ON sc_plan_monitor_item (supply_status, delay_class);
CREATE INDEX IF NOT EXISTS idx_sc_plan_monitor_item_snapshot ON sc_plan_monitor_item (snapshot_id);

COMMENT ON TABLE sc_plan_monitor_item IS '监控证据明细：任务对应的 BOM 物料供应证据';
COMMENT ON COLUMN sc_plan_monitor_item.delay_class IS 'A / B / none';

-- updated_at 自动刷新：对齐 MySQL 的 ON UPDATE CURRENT_TIMESTAMP(6) 语义
CREATE OR REPLACE FUNCTION sc_set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sc_plan_monitor_item_updated_at ON sc_plan_monitor_item;
CREATE TRIGGER trg_sc_plan_monitor_item_updated_at
    BEFORE UPDATE ON sc_plan_monitor_item
    FOR EACH ROW
    EXECUTE PROCEDURE sc_set_updated_at();

COMMIT;
