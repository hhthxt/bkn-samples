"""受管上下文层：resolved_context 合同与快照组装（无远程调用）。"""

from .assembler import (
    DEFAULT_MAX_AGE_SECONDS,
    EXPECTED_KNOWLEDGE_NETWORK_ID,
    ResolvedContextAssembler,
    compute_input_digest,
    snapshot_id_from_digest,
)
from .operation_contracts import ALLOWED_DATASETS, OPERATION_CONTRACTS, required_datasets
from .contract import (
    SOURCE_OFFLINE_TEST,
    SOURCE_OPENBKN,
    VALID_SOURCES,
    BknReceipt,
    ContextContractError,
    ContextRequired,
    ContextStale,
    ReceiptRequired,
    ResolvedContext,
    SchemaMismatch,
    SnapshotEnvelope,
    SnapshotIncomplete,
)

__all__ = [
    "DEFAULT_MAX_AGE_SECONDS",
    "EXPECTED_KNOWLEDGE_NETWORK_ID",
    "SOURCE_OFFLINE_TEST",
    "SOURCE_OPENBKN",
    "VALID_SOURCES",
    "ALLOWED_DATASETS",
    "OPERATION_CONTRACTS",
    "BknReceipt",
    "ContextContractError",
    "ContextRequired",
    "ContextStale",
    "ReceiptRequired",
    "ResolvedContext",
    "ResolvedContextAssembler",
    "SchemaMismatch",
    "SnapshotEnvelope",
    "SnapshotIncomplete",
    "compute_input_digest",
    "required_datasets",
    "snapshot_id_from_digest",
]
