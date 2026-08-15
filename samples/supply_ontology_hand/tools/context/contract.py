"""resolved_context 与 SnapshotEnvelope 输入合同（P0 设计 §3.3/§5.1）。

第三方 Agent 自己调用官方 Context Loader，把查询结果和 bkn_receipt 内联进
resolved_context。本模块只做结构校验、防御性复制和证据留存，不含任何远程
调用、凭据或客户端封装。
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any

from fn.snapshot import Snapshot

SOURCE_OPENBKN = "openbkn"
SOURCE_OFFLINE_TEST = "offline_test"
VALID_SOURCES = (SOURCE_OPENBKN, SOURCE_OFFLINE_TEST)


class ContextContractError(ValueError):
    """resolved_context 合同错误基类；code 对齐 P0 设计 §5.3。"""

    code = "context_error"


class ContextRequired(ContextContractError):
    code = "context_required"


class ReceiptRequired(ContextContractError):
    code = "receipt_required"


class ContextStale(ContextContractError):
    code = "context_stale"


class SnapshotIncomplete(ContextContractError):
    code = "snapshot_incomplete"


class SchemaMismatch(ContextContractError):
    code = "schema_mismatch"


def _parse_captured_at(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value.strip():
        text = value.strip()
        if text.endswith(("Z", "z")):
            text = f"{text[:-1]}+00:00"
        try:
            return datetime.fromisoformat(text)
        except ValueError as exc:
            raise SchemaMismatch(f"captured_at 不是合法 ISO 时间: {value!r}") from exc
    raise ContextRequired("captured_at 缺失")


@dataclass(frozen=True)
class BknReceipt:
    """一次 Context Loader 查询的取数凭据。

    本层只校验凭据存在且归属同一 Interaction，不做签名验证。
    """

    dataset: str
    interaction_id: str = ""
    resource_id: str | None = None
    query_type: str | None = None
    receipt_id: str | None = None
    row_count: int | None = None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> BknReceipt:
        if not isinstance(payload, Mapping):
            raise SchemaMismatch("bkn_receipt 必须是对象")
        return cls(
            dataset=str(payload.get("dataset") or "").strip(),
            interaction_id=str(payload.get("interaction_id") or "").strip(),
            resource_id=payload.get("resource_id"),
            query_type=payload.get("query_type"),
            receipt_id=payload.get("receipt_id"),
            row_count=payload.get("row_count"),
        )


def _freeze_rows(rows: Any) -> Mapping[str, tuple[dict[str, Any], ...]]:
    if rows is None:
        return MappingProxyType({})
    if not isinstance(rows, Mapping):
        raise SchemaMismatch("rows 必须是 逻辑数据集 -> 行数组 的映射")
    frozen: dict[str, tuple[dict[str, Any], ...]] = {}
    for name, dataset_rows in rows.items():
        if not isinstance(dataset_rows, Iterable) or isinstance(dataset_rows, (str, bytes, Mapping)):
            raise SchemaMismatch(f"数据集 {name} 必须是行数组")
        copied: list[dict[str, Any]] = []
        for row in dataset_rows:
            if not isinstance(row, Mapping):
                raise SchemaMismatch(f"数据集 {name} 的行必须是对象")
            copied.append(dict(row))
        frozen[str(name)] = tuple(copied)
    return MappingProxyType(frozen)


def _freeze_receipts(receipts: Any) -> tuple[BknReceipt, ...]:
    if not receipts:
        return ()
    if isinstance(receipts, (str, bytes, Mapping)):
        raise SchemaMismatch("bkn_receipts 必须是数组")
    frozen: list[BknReceipt] = []
    for receipt in receipts:
        if isinstance(receipt, BknReceipt):
            frozen.append(receipt)
        elif isinstance(receipt, Mapping):
            frozen.append(BknReceipt.from_payload(receipt))
        else:
            raise SchemaMismatch("bkn_receipt 必须是对象")
    return tuple(frozen)


@dataclass(frozen=True)
class ResolvedContext:
    """Agent 内联的一次性受管取数结果。"""

    knowledge_network_id: str
    conversation_id: str
    interaction_id: str
    captured_at: datetime
    rows: Mapping[str, tuple[dict[str, Any], ...]] = field(default_factory=dict)
    bkn_receipts: tuple[BknReceipt, ...] = ()

    def __post_init__(self) -> None:
        captured_at = self.captured_at
        if not isinstance(captured_at, datetime):
            raise ContextRequired("captured_at 必须是带时区的 datetime")
        if captured_at.tzinfo is None or captured_at.utcoffset() is None:
            raise ContextRequired("captured_at 必须带时区")
        object.__setattr__(self, "rows", _freeze_rows(self.rows))
        object.__setattr__(self, "bkn_receipts", _freeze_receipts(self.bkn_receipts))

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ResolvedContext:
        if not isinstance(payload, Mapping):
            raise ContextRequired("缺少 resolved_context")
        return cls(
            knowledge_network_id=str(payload.get("knowledge_network_id") or "").strip(),
            conversation_id=str(payload.get("conversation_id") or "").strip(),
            interaction_id=str(payload.get("interaction_id") or "").strip(),
            captured_at=_parse_captured_at(payload.get("captured_at")),
            rows=payload.get("rows") or {},
            bkn_receipts=payload.get("bkn_receipts") or (),
        )

    def receipts_for(self, dataset: str) -> tuple[BknReceipt, ...]:
        return tuple(r for r in self.bkn_receipts if r.dataset == dataset)


@dataclass(frozen=True)
class SnapshotEnvelope:
    """单次一致快照及其溯源信息（P0 设计 §3.2）。"""

    snapshot: Snapshot
    snapshot_id: str
    captured_at: datetime
    knowledge_network_id: str
    conversation_id: str
    interaction_id: str
    source: str
    bkn_receipts: tuple[BknReceipt, ...]
    loaded_datasets: tuple[str, ...]
    input_digest: str
