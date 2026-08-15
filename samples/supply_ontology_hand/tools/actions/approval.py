from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any

class ApprovalError(ValueError): pass
class ApprovalRequired(ApprovalError): pass
class ApprovalReplay(ApprovalError): pass
class ApprovalExpired(ApprovalError): pass
class ApprovalMismatch(ApprovalError): pass

def proposal_digest(proposal: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(proposal, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
def _b64(data: bytes) -> str: return base64.urlsafe_b64encode(data).decode().rstrip("=")
def _unb64(value: str) -> bytes: return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

class ApprovalAuthority:
    def __init__(self, secret: str):
        if not secret: raise ValueError("approval secret is required")
        self.secret = secret.encode()
    def issue(self, proposal: dict[str, Any], *, action_type: str, interaction_id: str, approver: str, idempotency_key: str, now: datetime, ttl_seconds: int = 900) -> str:
        if not approver or not interaction_id or not idempotency_key: raise ApprovalRequired("approval fields required")
        payload = {"proposal_hash": proposal_digest(proposal), "action_type": action_type, "interaction_id": interaction_id, "approver": approver, "idempotency_key": idempotency_key, "issued_at": now.astimezone(timezone.utc).isoformat(), "expires_at": (now + timedelta(seconds=ttl_seconds)).astimezone(timezone.utc).isoformat()}
        encoded = _b64(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())
        signature = _b64(hmac.new(self.secret, encoded.encode(), hashlib.sha256).digest())
        return f"{encoded}.{signature}"
    def verify(self, token: str | None, proposal: dict[str, Any], *, action_type: str, interaction_id: str, idempotency_key: str, now: datetime) -> dict[str, Any]:
        if not token: raise ApprovalRequired("approved token is required")
        try:
            encoded, signature = token.split(".", 1)
            expected = _b64(hmac.new(self.secret, encoded.encode(), hashlib.sha256).digest())
            if not hmac.compare_digest(signature, expected): raise ApprovalMismatch("invalid approval signature")
            payload = json.loads(_unb64(encoded).decode())
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ApprovalMismatch("malformed approval token") from exc
        if payload.get("proposal_hash") != proposal_digest(proposal): raise ApprovalMismatch("proposal hash mismatch")
        if payload.get("action_type") != action_type: raise ApprovalMismatch("action type mismatch")
        if payload.get("interaction_id") != interaction_id: raise ApprovalMismatch("interaction mismatch")
        if payload.get("idempotency_key") != idempotency_key: raise ApprovalMismatch("idempotency mismatch")
        if now.astimezone(timezone.utc) >= datetime.fromisoformat(payload["expires_at"]): raise ApprovalExpired("approval token expired")
        return payload
