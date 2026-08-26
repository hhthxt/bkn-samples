from __future__ import annotations

from datetime import date
from typing import Any

from context.assembler import ResolvedContextAssembler
from context.contract import SOURCE_OFFLINE_TEST
from context.operation_contracts import required_datasets
from fn import backward_plan, shared_contention, total_sellable
from .offline_provider import OfflineSnapshotProvider

DATASETS = frozenset({"forecast", "bom", "material", "inventory", "purchase_order", "purchase_request", "mrp"})


class FulfillmentCommitmentRunner:
    def __init__(self, data_dir: str):
        self.provider = OfflineSnapshotProvider(data_dir)
        self.assembler = ResolvedContextAssembler()

    def run(self, *, product: str, forecast_id: str, demand_end: str, demand_qty: float, substitute_enabled: bool, demands: list[dict[str, Any]] | None = None, report_grain: str = "summary", as_of_date: str = "2026-08-15") -> dict[str, Any]:
        if not forecast_id:
            raise ValueError("forecast_id is required")
        context = self.provider.capture(datasets=DATASETS, product=None if demands else product, forecast_id=forecast_id)
        envelope = self.assembler.assemble(context, required_datasets("backward_plan"), source=SOURCE_OFFLINE_TEST)
        s1 = backward_plan(envelope.snapshot, product, forecast_id=forecast_id, demand_end=demand_end, demand_qty=demand_qty, substitute_enabled=substitute_enabled, report_grain=report_grain, today=date.fromisoformat(as_of_date))
        s2 = total_sellable(envelope.snapshot, product, substitute_enabled=substitute_enabled)
        steps = [{"id": "s1", "name": "生产计划倒排与齐套诊断", "result": s1}, {"id": "s2", "name": "产品可售能力", "result": s2}]
        if demands:
            steps.append({"id": "s3", "name": "新需求覆盖与共享物料争用", "result": shared_contention(envelope.snapshot, demands, substitute_enabled=substitute_enabled)})
        proposals = []
        if not s1["can_deliver_on_time"] or s1["gaps"]:
            proposals.append({"action": "create_monitor_task", "status": "proposed"})
        if s1["gaps"]:
            proposals.append({"action": "create_pr_decision", "status": "proposed"})
        return {"scenario_id": "fulfillment-commitment", "story": "客户需求承诺前的供应链履约核查", "snapshot_meta": {"snapshot_id": envelope.snapshot_id, "captured_at": envelope.captured_at.isoformat(), "knowledge_network_id": envelope.knowledge_network_id, "conversation_id": envelope.conversation_id, "interaction_id": envelope.interaction_id, "source": envelope.source, "loaded_datasets": list(envelope.loaded_datasets), "input_digest": envelope.input_digest}, "steps": steps, "action_proposals": proposals}
