from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class OrganizationalMemoryRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    memory_id: str
    organization_id: str
    memory_type: str = "enterprise_fact"
    source: str = "system"
    subject: str = ""
    content: str = ""
    reference: str = ""
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    supersedes: str | None = None
    status: str = "active"


class OrganizationalMemoryStore:
    def __init__(self) -> None:
        self._store: dict[str, OrganizationalMemoryRecord] = {}

    def _key(self, org_id: str, mem_id: str) -> str:
        return f"{org_id}:{mem_id}"

    def create(self, organization_id: str, content: str, memory_type: str = "enterprise_fact", subject: str = "", source: str = "system", confidence: float = 0.8, provenance: dict[str, Any] | None = None, valid_from: datetime | None = None, valid_until: datetime | None = None, supersedes: str | None = None, reference: str = "") -> OrganizationalMemoryRecord:
        mid = f"orgmem-{uuid.uuid4().hex[:8]}"
        # sanitize provenance secrets
        prov = {k: v for k, v in (provenance or {}).items() if "secret" not in k.lower() and "token" not in k.lower() and "password" not in k.lower()}
        # add provenance chain SOURCE->EXTRACTION->TRANSFORMATION->KNOWLEDGE->USAGE
        prov.setdefault("chain", ["source", "extraction", "transformation", "knowledge", "usage"])
        rec = OrganizationalMemoryRecord(memory_id=mid, organization_id=organization_id, memory_type=memory_type, source=source, subject=subject, content=content, reference=reference, confidence=confidence, provenance=prov, valid_from=valid_from, valid_until=valid_until, supersedes=supersedes)
        self._store[self._key(organization_id, mid)] = rec
        # handle supersession: mark superseded as superseded
        if supersedes:
            old_key = self._key(organization_id, supersedes)
            old = self._store.get(old_key)
            if old:
                self._store[old_key] = old.model_copy(update={"status": "superseded"})
        return rec

    def get(self, memory_id: str, organization_id: str) -> OrganizationalMemoryRecord | None:
        return self._store.get(self._key(organization_id, memory_id))

    def list_for_tenant(self, organization_id: str, memory_type: str | None = None, subject: str | None = None, status: str | None = None, include_expired: bool = False) -> list[OrganizationalMemoryRecord]:
        prefix = f"{organization_id}:"
        out = [v for k, v in self._store.items() if k.startswith(prefix)]
        if memory_type:
            out = [r for r in out if r.memory_type == memory_type]
        if subject:
            out = [r for r in out if r.subject == subject]
        if status:
            out = [r for r in out if r.status == status]
        if not include_expired:
            now = datetime.now(UTC)
            out = [r for r in out if r.valid_until is None or r.valid_until > now]
        return out

    def temporal_query(self, organization_id: str, at: datetime) -> list[OrganizationalMemoryRecord]:
        out = self.list_for_tenant(organization_id, include_expired=True)
        result: list[OrganizationalMemoryRecord] = []
        for r in out:
            if r.valid_from and r.valid_from > at:
                continue
            if r.valid_until and r.valid_until <= at:
                continue
            result.append(r)
        return result

    def detect_stale(self, organization_id: str, days: int = 90) -> list[OrganizationalMemoryRecord]:
        from datetime import timedelta
        cutoff = datetime.now(UTC) - timedelta(days=days)
        return [r for r in self.list_for_tenant(organization_id) if r.created_at < cutoff and r.status == "active"]

    def detect_conflicts(self, organization_id: str) -> list[dict[str, Any]]:
        # simple: same subject, different content, both active -> potential conflict
        records = self.list_for_tenant(organization_id, status="active")
        by_subject: dict[str, list[OrganizationalMemoryRecord]] = {}
        for r in records:
            if r.subject:
                by_subject.setdefault(r.subject, []).append(r)
        conflicts: list[dict[str, Any]] = []
        for subj, lst in by_subject.items():
            if len(lst) > 1:
                contents = {r.content for r in lst}
                if len(contents) > 1:
                    conflicts.append({"subject": subj, "memory_ids": [r.memory_id for r in lst], "count": len(lst)})
        return conflicts

    def maintenance_proposals(self, organization_id: str) -> list[dict[str, Any]]:
        proposals: list[dict[str, Any]] = []
        for r in self.detect_stale(organization_id):
            proposals.append({"action": "supersede", "memory_id": r.memory_id, "reason": "stale", "requires_approval": True})
        for c in self.detect_conflicts(organization_id):
            proposals.append({"action": "reconcile", "subject": c["subject"], "memory_ids": c["memory_ids"], "reason": "conflict", "requires_approval": True})
        return proposals


__all__ = ["OrganizationalMemoryRecord", "OrganizationalMemoryStore"]
