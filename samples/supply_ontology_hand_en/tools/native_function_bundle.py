"""Build the self-contained OpenBKN native Function payload.

The Foundry Function Runtime accepts one Python source string and executes a
``handler(event)`` entrypoint in an isolated sandbox.  This builder packages
the existing pure calculation and context-contract modules into that source;
it deliberately contains no network client, database client, or service URL.
"""

from __future__ import annotations

import base64
import io
import textwrap
import zipfile
from pathlib import Path


TOOLS = Path(__file__).resolve().parent
PACKAGE_PATHS = (TOOLS / "fn", TOOLS / "context")


ENTRY_SOURCE = r'''
from context.assembler import ResolvedContextAssembler
from context.contract import ResolvedContext
from context.operation_contracts import required_datasets
from fn import (
    backward_plan, bom_list, bom_shared_list, kitting_net_demand,
    layered_inventory, leadtime_days, max_build_without_po,
    open_forecast_count, shared_contention, substitute_status,
    supply_status, theoretical_build, total_sellable,
)


def _snapshot_meta(envelope):
    return {
        "snapshot_id": envelope.snapshot_id,
        "captured_at": envelope.captured_at.isoformat(),
        "knowledge_network_id": envelope.knowledge_network_id,
        "conversation_id": envelope.conversation_id,
        "interaction_id": envelope.interaction_id,
        "source": envelope.source,
        "loaded_datasets": list(envelope.loaded_datasets),
        "input_digest": envelope.input_digest,
    }


def execute(event):
    operation = str(event.get("operation") or "").strip()
    params = event.get("parameters") or {}
    if not isinstance(params, dict):
        raise ValueError("parameters must be an object")
    context_payload = params.get("resolved_context")
    ctx = ResolvedContext.from_payload(context_payload)
    envelope = ResolvedContextAssembler().assemble(
        ctx, required_datasets(operation), source="openbkn"
    )
    snap = envelope.snapshot
    product = params.get("product")
    if operation == "bom_list":
        result = bom_list(snap, product, depth=params.get("depth", 1), include_substitute=params.get("include_substitute", False))
    elif operation == "bom_shared_list":
        result = bom_shared_list(snap, params.get("products") or [], depth=params.get("depth"), include_substitute=params.get("include_substitute", False))
    elif operation == "layered_inventory":
        result = layered_inventory(snap, product, depth=params.get("depth", 1), warehouse_scope=params.get("warehouse_scope", "production_available"), include_substitute=params.get("include_substitute", False))
    elif operation == "substitute_status":
        result = substitute_status(snap, product, warehouse_scope=params.get("warehouse_scope", "production_available"), substitute_enabled=params.get("substitute_enabled"))
    elif operation == "theoretical_build":
        result = theoretical_build(snap, product, warehouse_scope=params.get("warehouse_scope", "production_available"), substitute_enabled=params.get("substitute_enabled"))
    elif operation == "total_sellable":
        result = total_sellable(snap, product, production_scope=params.get("production_scope", "production_available"), finished_goods_scope=params.get("finished_goods_scope", "finished_goods"), substitute_enabled=params.get("substitute_enabled"))
    elif operation == "kitting_net_demand":
        result = kitting_net_demand(snap, product, params.get("qty"), warehouse_scope=params.get("warehouse_scope", "production_available"), substitute_enabled=params.get("substitute_enabled"))
    elif operation == "shared_contention":
        result = shared_contention(snap, params.get("demands") or [], warehouse_scope=params.get("warehouse_scope", "production_available"), substitute_enabled=params.get("substitute_enabled"))
    elif operation == "max_build_without_po":
        result = max_build_without_po(snap, product, warehouse_scope=params.get("warehouse_scope", "production_available"), substitute_enabled=params.get("substitute_enabled"))
    elif operation == "leadtime_days":
        material_code = params.get("material_code")
        result = {"material_code": material_code, "leadtime_days": leadtime_days(snap, material_code)}
    elif operation == "supply_status":
        result = supply_status(snap, params.get("material_code"), due_date=params.get("due_date"), gross_requirement=params.get("gross_requirement", 0), warehouse_scope=params.get("warehouse_scope", "production_available"), child_short=params.get("child_short", False))
    elif operation == "open_forecast_count":
        result = open_forecast_count(params["resolved_context"].get("rows", {}).get("forecast") or [], product_code=params.get("product_code"))
    elif operation == "backward_plan":
        result = backward_plan(snap, product, forecast_id=params.get("forecast_id"), demand_end=params.get("demand_end"), demand_qty=params.get("demand_qty"), warehouse_scope=params.get("warehouse_scope", "production_available"), substitute_enabled=params.get("substitute_enabled"), report_grain=params.get("report_grain", "summary"))
    else:
        raise ValueError("unsupported operation: %s" % operation)
    result["snapshot_meta"] = _snapshot_meta(envelope)
    return result
'''


def _archive_source() -> str:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for package in PACKAGE_PATHS:
            for file_path in sorted(package.rglob("*.py")):
                archive.write(file_path, file_path.relative_to(TOOLS))
        archive.writestr("supply_native_entry.py", textwrap.dedent(ENTRY_SOURCE).lstrip())
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def build_native_function_code() -> str:
    """Return Foundry-compatible, self-contained ``handler(event)`` code."""
    encoded = _archive_source()
    return textwrap.dedent(
        f'''\
        import base64
        import io
        import sys
        import tempfile
        import zipfile

        _SUPPLY_SOURCE = {encoded!r}
        _SUPPLY_EXECUTE = None

        def _load_supply_execute():
            global _SUPPLY_EXECUTE
            if _SUPPLY_EXECUTE is None:
                root = tempfile.mkdtemp(prefix="supply_native_function_")
                with zipfile.ZipFile(io.BytesIO(base64.b64decode(_SUPPLY_SOURCE))) as archive:
                    archive.extractall(root)
                sys.path.insert(0, root)
                from supply_native_entry import execute
                _SUPPLY_EXECUTE = execute
            return _SUPPLY_EXECUTE

        def handler(event):
            if not isinstance(event, dict):
                raise ValueError("event must be an object")
            return _load_supply_execute()(event)
        '''
    )
