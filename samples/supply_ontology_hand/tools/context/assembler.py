"""ResolvedContextAssembler：校验受管上下文并组装 SnapshotEnvelope。

只做校验、标准化、快照组装和输入摘要哈希；不查询远端、不缓存业务数据、
运行时不回退 CSV（P0 设计 §3.1/§3.3/§5.2）。
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from fn.snapshot import Snapshot, build_snapshot

from .contract import (
    SOURCE_OFFLINE_TEST,
    SOURCE_OPENBKN,
    VALID_SOURCES,
    ContextRequired,
    ContextStale,
    ReceiptRequired,
    ResolvedContext,
    SchemaMismatch,
    SnapshotEnvelope,
    SnapshotIncomplete,
)

DEFAULT_MAX_AGE_SECONDS = 900
EXPECTED_KNOWLEDGE_NETWORK_ID = "supply_ontology_hand"
SNAPSHOT_ID_PREFIX = "snap_"
SNAPSHOT_ID_DIGEST_CHARS = 16


def compute_input_digest(rows_by_dataset: Mapping[str, Iterable[Mapping[str, Any]]]) -> str:
    """规范 JSON 后 SHA-256；同一规范输入稳定，输入变化摘要变化。"""
    canonical = {
        str(name): [dict(row) for row in (dataset_rows or ())]
        for name, dataset_rows in (rows_by_dataset or {}).items()
    }
    text = json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def snapshot_id_from_digest(input_digest: str) -> str:
    return f"{SNAPSHOT_ID_PREFIX}{input_digest[:SNAPSHOT_ID_DIGEST_CHARS]}"


class ResolvedContextAssembler:
    def __init__(
        self,
        *,
        knowledge_network_id: str = EXPECTED_KNOWLEDGE_NETWORK_ID,
        max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.knowledge_network_id = knowledge_network_id
        self.max_age_seconds = max_age_seconds
        self._now = now or (lambda: datetime.now(timezone.utc))

    def assemble(
        self,
        ctx: ResolvedContext | None,
        required_datasets: Iterable[str],
        *,
        source: str = SOURCE_OPENBKN,
    ) -> SnapshotEnvelope:
        if source not in VALID_SOURCES:
            raise SchemaMismatch(f"source 必须是 {VALID_SOURCES} 之一，收到 {source!r}")
        if ctx is None:
            raise ContextRequired("缺少 resolved_context")
        if not isinstance(ctx, ResolvedContext):
            raise SchemaMismatch("resolved_context 不符合合同类型")

        datasets = tuple(sorted({str(name).strip() for name in required_datasets if str(name).strip()}))
        if not datasets:
            raise SnapshotIncomplete("required_datasets 不能为空")

        if source == SOURCE_OPENBKN:
            self._check_managed_context(ctx)

        missing = [name for name in datasets if name not in ctx.rows]
        if missing:
            raise SnapshotIncomplete(f"缺少必需数据集: {', '.join(missing)}")

        loaded_rows = {name: ctx.rows[name] for name in datasets}

        if source == SOURCE_OPENBKN:
            self._check_receipts(ctx, loaded_rows)

        input_digest = compute_input_digest(loaded_rows)
        return SnapshotEnvelope(
            snapshot=self._build_snapshot(loaded_rows),
            snapshot_id=snapshot_id_from_digest(input_digest),
            captured_at=ctx.captured_at,
            knowledge_network_id=ctx.knowledge_network_id,
            conversation_id=ctx.conversation_id,
            interaction_id=ctx.interaction_id,
            source=source,
            bkn_receipts=ctx.bkn_receipts,
            loaded_datasets=datasets,
            input_digest=input_digest,
        )

    @staticmethod
    def _build_snapshot(
        loaded_rows: Mapping[str, tuple[dict[str, Any], ...]],
    ) -> Snapshot:
        """快照组装期的数据一致性错误统一转成合同错误，不向调用方泄露 ValueError。"""
        try:
            return build_snapshot(loaded_rows)
        except ValueError as exc:
            raise SchemaMismatch(f"快照组装失败: {exc}") from exc

    def _check_managed_context(self, ctx: ResolvedContext) -> None:
        if (ctx.knowledge_network_id or "").strip() != self.knowledge_network_id:
            raise ContextRequired(
                f"知识网络必须是 {self.knowledge_network_id}，收到 {ctx.knowledge_network_id!r}"
            )
        if not (ctx.conversation_id or "").strip():
            raise ContextRequired("conversation_id 不能为空")
        if not (ctx.interaction_id or "").strip():
            raise ContextRequired("interaction_id 不能为空")

        reference = self._now()
        if reference.tzinfo is None:
            reference = reference.replace(tzinfo=timezone.utc)
        age_seconds = (reference - ctx.captured_at).total_seconds()
        if age_seconds > self.max_age_seconds:
            raise ContextStale(
                f"快照已超过允许时效 {self.max_age_seconds}s（实际 {age_seconds:.0f}s）"
            )

    def _check_receipts(
        self,
        ctx: ResolvedContext,
        loaded_rows: Mapping[str, tuple[dict[str, Any], ...]],
    ) -> None:
        interaction_id = ctx.interaction_id.strip()
        without_receipt = [
            name
            for name, rows in loaded_rows.items()
            if rows
            and not any(
                receipt.interaction_id.strip() == interaction_id
                for receipt in ctx.receipts_for(name)
            )
        ]
        if without_receipt:
            raise ReceiptRequired(
                "以下远程数据集缺少归属 interaction "
                f"{interaction_id} 的 BKN receipt: {', '.join(sorted(without_receipt))}"
            )


__all__ = [
    "DEFAULT_MAX_AGE_SECONDS",
    "EXPECTED_KNOWLEDGE_NETWORK_ID",
    "SOURCE_OFFLINE_TEST",
    "SOURCE_OPENBKN",
    "ResolvedContextAssembler",
    "compute_input_digest",
    "snapshot_id_from_digest",
]
