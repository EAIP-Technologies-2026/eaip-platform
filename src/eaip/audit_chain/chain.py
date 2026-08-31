from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from eaip.audit_chain.models import AuditChainRecord
from eaip.shared.time import utc_now


def _hash_record(record_id: str, tenant_id: str, actor: str, action: str, previous_hash: str, timestamp: str) -> str:
    payload = f"{record_id}|{tenant_id}|{actor}|{action}|{previous_hash}|{timestamp}"
    return hashlib.sha256(payload.encode()).hexdigest()


class AuditChain:
    def __init__(self) -> None:
        self._records: list[AuditChainRecord] = []
        self._by_tenant: dict[str, list[AuditChainRecord]] = {}

    def append(self, tenant_id: str, actor: str, action: str, metadata: dict[str, Any] | None = None) -> AuditChainRecord:
        previous_hash = self._by_tenant.get(tenant_id, [])[-1].record_hash if self._by_tenant.get(tenant_id) else ""
        record_id = f"audit-{uuid.uuid4().hex[:12]}"
        ts = utc_now()
        record_hash = _hash_record(record_id, tenant_id, actor, action, previous_hash, ts.isoformat())
        safe_meta = {k: v for k, v in (metadata or {}).items() if "secret" not in k.lower() and "password" not in k.lower() and "token" not in k.lower()}
        rec = AuditChainRecord(record_id=record_id, tenant_id=tenant_id, actor=actor, action=action, previous_hash=previous_hash, record_hash=record_hash, timestamp=ts, metadata=safe_meta)
        self._records.append(rec)
        self._by_tenant.setdefault(tenant_id, []).append(rec)
        return rec

    def list_for_tenant(self, tenant_id: str) -> list[AuditChainRecord]:
        return list(self._by_tenant.get(tenant_id, []))

    def append_execution(self, tenant_id: str, actor: str, execution_id: str, inputs_hash: str = "", policy_hash: str = "", tool_hash: str = "", output_hash: str = "") -> AuditChainRecord:
        import hashlib as _hl
        # inputs/policy/tool/output hashes are SHA-256 of canonical payloads (never secrets)
        ph = _hl.sha256(f"{inputs_hash}|{policy_hash}|{tool_hash}|{output_hash}".encode()).hexdigest() if any([inputs_hash, policy_hash, tool_hash, output_hash]) else ""
        return self.append(tenant_id=tenant_id, actor=actor, action=f"execution:{execution_id}", metadata={"execution_id": execution_id, "inputs_hash": inputs_hash, "policy_hash": policy_hash, "tool_hash": tool_hash, "output_hash": output_hash, "combined_hash": ph})

    def verify_execution(self, tenant_id: str, record_id: str) -> dict[str, Any]:
        for rec in self._by_tenant.get(tenant_id, []):
            if rec.record_id == record_id:
                expected = _hash_record(rec.record_id, rec.tenant_id, rec.actor, rec.action, rec.previous_hash, rec.timestamp.isoformat())
                return {"valid": rec.record_hash == expected, "record_id": record_id, "record_hash": rec.record_hash, "expected_hash": expected}
        return {"valid": False, "reason": "not found", "record_id": record_id}

    def verify(self, tenant_id: str) -> dict[str, Any]:
        records = self._by_tenant.get(tenant_id, [])
        if not records:
            return {"valid": True, "count": 0}
        for i, rec in enumerate(records):
            expected_prev = records[i - 1].record_hash if i > 0 else ""
            if rec.previous_hash != expected_prev:
                return {"valid": False, "count": len(records), "broken_at": rec.record_id}
            expected_hash = _hash_record(rec.record_id, rec.tenant_id, rec.actor, rec.action, rec.previous_hash, rec.timestamp.isoformat())
            if rec.record_hash != expected_hash:
                return {"valid": False, "count": len(records), "tampered_at": rec.record_id}
        return {"valid": True, "count": len(records)}
