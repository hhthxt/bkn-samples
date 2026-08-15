"""Runtime dependencies for the function service. No remote clients."""

from __future__ import annotations

from context.assembler import ResolvedContextAssembler
from context.contract import SOURCE_OPENBKN

CONTRACT_VERSION = "2026-08-14"


def get_snapshot_source() -> str:
    """Production default: Agent-supplied OpenBKN context. Tests may override."""
    return SOURCE_OPENBKN


def get_assembler() -> ResolvedContextAssembler:
    return ResolvedContextAssembler()
