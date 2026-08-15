#!/usr/bin/env python3
"""OpenAPI service for the supply_ontology_hand function toolbox.

Agents query Context Loader themselves and inline resolved_context.
This service never connects to OpenBKN or reads CSV at runtime.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from context.assembler import ResolvedContextAssembler
from context.contract import (
    ContextContractError,
    ContextStale,
    ResolvedContext,
)
from context.operation_contracts import required_datasets
from fn import (
    CannotCompute,
    backward_plan,
    bom_list,
    bom_shared_list,
    kitting_net_demand,
    layered_inventory,
    leadtime_days,
    max_build_without_po,
    open_forecast_count,
    shared_contention,
    substitute_status,
    supply_status,
    theoretical_build,
    total_sellable,
)
from service_dependencies import CONTRACT_VERSION, get_assembler, get_snapshot_source


KN_ID = "supply_ontology_hand"

app = FastAPI(
    title="供应链计算函数工具箱",
    description=(
        "面向 supply_ontology_hand 的 BOM、库存、可产、可售、齐套、争用和交期函数。"
        "调用方必须内联 resolved_context。理论可产、合计可售、齐套净需求是不同口径；替代组使用 MAX。"
    ),
    version="0.2.0",
)


class ResolvedContextRequest(BaseModel):
    knowledge_network_id: str
    conversation_id: str
    interaction_id: str
    captured_at: datetime
    bkn_receipts: list[dict[str, Any]] = Field(default_factory=list)
    rows: dict[str, list[dict[str, Any]]]


class ToolRequest(BaseModel):
    resolved_context: ResolvedContextRequest


class ProductRequest(ToolRequest):
    product: str = Field(description="产品编码")
    warehouse_scope: str | list[str] | None = Field(
        default="production_available",
        description="仓范围预设 production_available/finished_goods/all，或显式仓列表",
    )


class BomListRequest(ToolRequest):
    product: str = Field(description="产品编码")
    depth: int | None = Field(default=1, ge=1, description="展开层数；null 表示全层级")
    include_substitute: bool = Field(default=False, description="是否包含替代料行")


class BomSharedRequest(ToolRequest):
    products: list[str] = Field(description="至少两个产品编码")
    depth: int | None = Field(default=None, ge=1, description="展开层数；null 表示全层级")
    include_substitute: bool = Field(default=False, description="是否包含替代料行")


class LayeredInventoryRequest(ProductRequest):
    depth: int | None = Field(default=1, ge=1, description="展开层数；null 表示全层级")
    include_substitute: bool = Field(default=False, description="是否包含替代料")


class SubstituteStatusRequest(ProductRequest):
    substitute_enabled: bool | None = Field(
        default=None, description="是否启用替代；未确认时传 null"
    )


class CapacityRequest(ProductRequest):
    substitute_enabled: bool | None = Field(
        description="必须明确是否启用替代料"
    )


class SellableRequest(ToolRequest):
    product: str = Field(description="产品编码")
    production_scope: str | list[str] | None = Field(
        default="production_available", description="理论可产的生产仓范围"
    )
    finished_goods_scope: str | list[str] | None = Field(
        default="finished_goods", description="成品库存仓范围"
    )
    substitute_enabled: bool | None = Field(
        description="必须明确是否启用替代料"
    )


class KittingRequest(ProductRequest):
    qty: float = Field(ge=0, description="需求套数 X")
    substitute_enabled: bool | None = Field(
        description="必须明确是否启用替代料"
    )


class Demand(BaseModel):
    product_code: str = Field(description="产品编码")
    qty: float = Field(ge=0, description="需求数量")


class ContentionRequest(ToolRequest):
    demands: list[Demand] = Field(
        min_length=2, description="至少两条需求；数组顺序即扣减顺序"
    )
    warehouse_scope: str | list[str] | None = Field(
        default="production_available", description="生产可用仓范围"
    )
    substitute_enabled: bool | None = Field(
        description="必须明确是否启用替代料"
    )


class LeadtimeRequest(ToolRequest):
    material_code: str = Field(description="物料编码")


class SupplyStatusRequest(ToolRequest):
    material_code: str = Field(description="物料编码")
    due_date: str | None = Field(
        default=None, description="到位日 YYYY-MM-DD；缺失时返回 unknown"
    )
    gross_requirement: float = Field(default=0, ge=0, description="毛需求")
    warehouse_scope: str | list[str] | None = Field(
        default="production_available", description="生产可用仓范围"
    )
    child_short: bool = Field(default=False, description="自制件的子件是否短缺")


class OpenForecastCountRequest(ToolRequest):
    product_code: str | None = Field(
        default=None, description="可选产品编码，对应 forecast.material_number"
    )


class BackwardPlanRequest(ToolRequest):
    product: str = Field(description="产品编码")
    forecast_id: str = Field(description="单张需求预测单 ID")
    demand_end: str = Field(description="需求截止日 YYYY-MM-DD")
    demand_qty: float = Field(gt=0, description="需求数量，须与预测单一致")
    warehouse_scope: str | list[str] | None = Field(
        default="production_available",
        description="仓范围预设 production_available/finished_goods/all，或显式仓列表",
    )
    substitute_enabled: bool = Field(description="必须明确是否启用替代料")
    report_grain: str = Field(default="summary", description="summary 或 full_tree")


def _assemble(
    operation_id: str,
    body: ToolRequest,
    source: str,
    assembler: ResolvedContextAssembler,
):
    ctx = ResolvedContext.from_payload(body.resolved_context.model_dump(mode="json"))
    return assembler.assemble(ctx, required_datasets(operation_id), source=source)


def _with_meta(result: dict[str, Any], envelope) -> dict[str, Any]:
    return {
        **result,
        "snapshot_meta": {
            "snapshot_id": envelope.snapshot_id,
            "captured_at": envelope.captured_at.isoformat(),
            "knowledge_network_id": envelope.knowledge_network_id,
            "conversation_id": envelope.conversation_id,
            "interaction_id": envelope.interaction_id,
            "source": envelope.source,
            "loaded_datasets": list(envelope.loaded_datasets),
            "input_digest": envelope.input_digest,
        },
    }


@app.exception_handler(CannotCompute)
async def cannot_compute_handler(
    _request: Request, exc: CannotCompute
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": {"error": "cannot_compute", "message": str(exc)}},
    )


@app.exception_handler(ContextContractError)
async def context_contract_handler(
    _request: Request, exc: ContextContractError
) -> JSONResponse:
    status = 409 if isinstance(exc, ContextStale) else 422
    return JSONResponse(
        status_code=status,
        content={"detail": {"error": exc.code, "message": str(exc)}},
    )


@app.exception_handler(RequestValidationError)
async def validation_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    if any(err.get("loc") and err["loc"][-1] == "resolved_context" for err in exc.errors()):
        return JSONResponse(
            status_code=422,
            content={"detail": {"error": "context_required", "message": "缺少 resolved_context"}},
        )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok", "knowledge_network_id": KN_ID}


def registered_operation_ids() -> list[str]:
    """只报告已注册为业务 Tool 的 route，避免宣称尚未暴露的合同 operation。"""
    return sorted(
        route.operation_id
        for route in app.routes
        if getattr(route, "operation_id", None) and getattr(route, "include_in_schema", False)
    )


@app.get("/ready", include_in_schema=False)
def ready(source: str = Depends(get_snapshot_source)) -> dict[str, Any]:
    return {
        "status": "ok",
        "knowledge_network_id": KN_ID,
        "snapshot_source": source,
        "contract_version": CONTRACT_VERSION,
        "operations": registered_operation_ids(),
    }


@app.post(
    "/functions/bom-list",
    operation_id="bom_list",
    summary="BOM清单",
    description="返回 BOM 结构和行数，不带库存。",
)
def bom_list_tool(
    body: BomListRequest,
    source: str = Depends(get_snapshot_source),
    assembler: ResolvedContextAssembler = Depends(get_assembler),
) -> dict[str, Any]:
    envelope = _assemble("bom_list", body, source, assembler)
    return _with_meta(
        bom_list(
            envelope.snapshot,
            body.product,
            depth=body.depth,
            include_substitute=body.include_substitute,
        ),
        envelope,
    )


@app.post(
    "/functions/bom-shared-list",
    operation_id="bom_shared_list",
    summary="产品BOM共用清单",
    description="求至少两个产品 BOM 子件的全集交集；不是库存争用判断。",
)
def bom_shared_list_tool(
    body: BomSharedRequest,
    source: str = Depends(get_snapshot_source),
    assembler: ResolvedContextAssembler = Depends(get_assembler),
) -> dict[str, Any]:
    envelope = _assemble("bom_shared_list", body, source, assembler)
    return _with_meta(
        bom_shared_list(
            envelope.snapshot,
            body.products,
            depth=body.depth,
            include_substitute=body.include_substitute,
        ),
        envelope,
    )


@app.post(
    "/functions/layered-inventory",
    operation_id="layered_inventory",
    summary="子料分层库存",
)
def layered_inventory_tool(
    body: LayeredInventoryRequest,
    source: str = Depends(get_snapshot_source),
    assembler: ResolvedContextAssembler = Depends(get_assembler),
) -> dict[str, Any]:
    envelope = _assemble("layered_inventory", body, source, assembler)
    return _with_meta(
        layered_inventory(
            envelope.snapshot,
            body.product,
            depth=body.depth,
            warehouse_scope=body.warehouse_scope,
            include_substitute=body.include_substitute,
        ),
        envelope,
    )


@app.post(
    "/functions/substitute-status",
    operation_id="substitute_status",
    summary="替代料状态",
)
def substitute_status_tool(
    body: SubstituteStatusRequest,
    source: str = Depends(get_snapshot_source),
    assembler: ResolvedContextAssembler = Depends(get_assembler),
) -> dict[str, Any]:
    envelope = _assemble("substitute_status", body, source, assembler)
    return _with_meta(
        substitute_status(
            envelope.snapshot,
            body.product,
            warehouse_scope=body.warehouse_scope,
            substitute_enabled=body.substitute_enabled,
        ),
        envelope,
    )


@app.post(
    "/functions/theoretical-build",
    operation_id="theoretical_build",
    summary="理论可产",
    description="生产可用库存除以叶子单耗后取最小值；不含成品和在途。",
)
def theoretical_build_tool(
    body: CapacityRequest,
    source: str = Depends(get_snapshot_source),
    assembler: ResolvedContextAssembler = Depends(get_assembler),
) -> dict[str, Any]:
    envelope = _assemble("theoretical_build", body, source, assembler)
    return _with_meta(
        theoretical_build(
            envelope.snapshot,
            body.product,
            warehouse_scope=body.warehouse_scope,
            substitute_enabled=body.substitute_enabled,
        ),
        envelope,
    )


@app.post(
    "/functions/total-sellable",
    operation_id="total_sellable",
    summary="合计可售",
    description="成品仓可用 + 理论可产；不含在途。",
)
def total_sellable_tool(
    body: SellableRequest,
    source: str = Depends(get_snapshot_source),
    assembler: ResolvedContextAssembler = Depends(get_assembler),
) -> dict[str, Any]:
    envelope = _assemble("total_sellable", body, source, assembler)
    return _with_meta(
        total_sellable(
            envelope.snapshot,
            body.product,
            production_scope=body.production_scope,
            finished_goods_scope=body.finished_goods_scope,
            substitute_enabled=body.substitute_enabled,
        ),
        envelope,
    )


@app.post(
    "/functions/kitting-net-demand",
    operation_id="kitting_net_demand",
    summary="要X套净需求与齐套",
    description="净需求=max(0, X×单耗-可用-未关闭PO未清)。",
)
def kitting_net_demand_tool(
    body: KittingRequest,
    source: str = Depends(get_snapshot_source),
    assembler: ResolvedContextAssembler = Depends(get_assembler),
) -> dict[str, Any]:
    envelope = _assemble("kitting_net_demand", body, source, assembler)
    return _with_meta(
        kitting_net_demand(
            envelope.snapshot,
            body.product,
            body.qty,
            warehouse_scope=body.warehouse_scope,
            substitute_enabled=body.substitute_enabled,
        ),
        envelope,
    )


@app.post(
    "/functions/shared-contention",
    operation_id="shared_contention",
    summary="共用料与多需求争用",
    description="共享可用与在途按 demands 数组顺序扣减。",
)
def shared_contention_tool(
    body: ContentionRequest,
    source: str = Depends(get_snapshot_source),
    assembler: ResolvedContextAssembler = Depends(get_assembler),
) -> dict[str, Any]:
    envelope = _assemble("shared_contention", body, source, assembler)
    return _with_meta(
        shared_contention(
            envelope.snapshot,
            [d.model_dump() for d in body.demands],
            warehouse_scope=body.warehouse_scope,
            substitute_enabled=body.substitute_enabled,
        ),
        envelope,
    )


@app.post(
    "/functions/max-build-without-po",
    operation_id="max_build_without_po",
    summary="无需采购最大可产",
    description="与理论可产同口径，不含成品库存和在途。",
)
def max_build_without_po_tool(
    body: CapacityRequest,
    source: str = Depends(get_snapshot_source),
    assembler: ResolvedContextAssembler = Depends(get_assembler),
) -> dict[str, Any]:
    envelope = _assemble("max_build_without_po", body, source, assembler)
    return _with_meta(
        max_build_without_po(
            envelope.snapshot,
            body.product,
            warehouse_scope=body.warehouse_scope,
            substitute_enabled=body.substitute_enabled,
        ),
        envelope,
    )


@app.post(
    "/functions/leadtime",
    operation_id="leadtime_days",
    summary="标准交期",
    description="外购/委外取采购提前期，自制取生产提前期。",
)
def leadtime_days_tool(
    body: LeadtimeRequest,
    source: str = Depends(get_snapshot_source),
    assembler: ResolvedContextAssembler = Depends(get_assembler),
) -> dict[str, Any]:
    envelope = _assemble("leadtime_days", body, source, assembler)
    return _with_meta(
        {
            "material_code": body.material_code,
            "leadtime_days": leadtime_days(envelope.snapshot, body.material_code),
        },
        envelope,
    )


@app.post(
    "/functions/supply-status",
    operation_id="supply_status",
    summary="供应状态10档S1内部",
    description="仅用于有到位日和毛需求的 S1；无到位日返回 unknown。",
)
def supply_status_tool(
    body: SupplyStatusRequest,
    source: str = Depends(get_snapshot_source),
    assembler: ResolvedContextAssembler = Depends(get_assembler),
) -> dict[str, Any]:
    envelope = _assemble("supply_status", body, source, assembler)
    return _with_meta(
        supply_status(
            envelope.snapshot,
            body.material_code,
            due_date=body.due_date,
            gross_requirement=body.gross_requirement,
            warehouse_scope=body.warehouse_scope,
            child_short=body.child_short,
        ),
        envelope,
    )


@app.post(
    "/functions/open-forecast-count",
    operation_id="open_forecast_count",
    summary="未关闭预测单数",
    description="对内联 forecast 行强制排除 closestatus_title 为已关闭的记录。",
)
def open_forecast_count_tool(
    body: OpenForecastCountRequest,
    source: str = Depends(get_snapshot_source),
    assembler: ResolvedContextAssembler = Depends(get_assembler),
) -> dict[str, Any]:
    envelope = _assemble("open_forecast_count", body, source, assembler)
    return _with_meta(
        open_forecast_count(
            body.resolved_context.rows.get("forecast") or [],
            product_code=body.product_code,
        ),
        envelope,
    )


@app.post(
    "/functions/backward-plan",
    operation_id="backward_plan",
    summary="生产计划齐套倒排",
    description="对一个产品加一张需求预测做日历日齐套倒排；调用方必须内联 resolved_context。",
)
def backward_plan_tool(
    body: BackwardPlanRequest,
    source: str = Depends(get_snapshot_source),
    assembler: ResolvedContextAssembler = Depends(get_assembler),
) -> dict[str, Any]:
    envelope = _assemble("backward_plan", body, source, assembler)
    return _with_meta(
        backward_plan(
            envelope.snapshot,
            body.product,
            forecast_id=body.forecast_id,
            demand_end=body.demand_end,
            demand_qty=body.demand_qty,
            warehouse_scope=body.warehouse_scope,
            substitute_enabled=body.substitute_enabled,
            report_grain=body.report_grain,
        ),
        envelope,
    )
