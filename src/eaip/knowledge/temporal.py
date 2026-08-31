from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class TemporalKnowledgeRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    record_id: str
    organization_id: str
    subject: str = ""
    content: str = ""
    valid_from: datetime = Field(default_factory=utc_now)
    valid_until: datetime | None = None
    supersedes: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    status: str = "active"
    created_at: datetime = Field(default_factory=utc_now)
    version: int = 1


class TemporalKnowledgeStore:
    def __init__(self) -> None:
        self._store: dict[str, TemporalKnowledgeRecord] = {}

    def _key(self, org_id: str, rid: str) -> str:
        return f"{org_id}:{rid}"

    def create(self, organization_id: str, subject: str, content: str, valid_from: datetime | None = None, valid_until: datetime | None = None, provenance: dict[str, Any] | None = None, supersedes: str | None = None) -> TemporalKnowledgeRecord:
        import uuid
        rid = f"tk-{uuid.uuid4().hex[:8]}"
        prov = {k: v for k, v in (provenance or {}).items() if "secret" not in k.lower() and "token" not in k.lower()}
        prov.setdefault("chain", ["source", "extraction", "transformation", "knowledge", "usage"])
        existing = None
        if supersedes:
            old_key = self._key(organization_id, supersedes)
            old = self._store.get(old_key)
            if old:
                existing = old
                self._store[old_key] = old.model_copy(update={"status": "superseded", "valid_until": valid_from or datetime.now(UTC)})
        rec = TemporalKnowledgeRecord(record_id=rid, organization_id=organization_id, subject=subject, content=content, valid_from=valid_from or datetime.now(UTC), valid_until=valid_until, supersedes=supersedes, provenance=prov, version=(existing.version + 1 if existing else 1))
        self._store[self._key(organization_id, rid)] = rec
        return rec

    def get(self, record_id: str, organization_id: str) -> TemporalKnowledgeRecord | None:
        return self._store.get(self._key(organization_id, record_id))

    def temporal_query(self, organization_id: str, at: datetime, subject: str | None = None) -> list[TemporalKnowledgeRecord]:
        prefix = f"{organization_id}:"
        out = [v for k, v in self._store.items() if k.startswith(prefix)]
        if subject:
            out = [r for r in out if r.subject == subject]
        result: list[TemporalKnowledgeRecord] = []
        for r in out:
            if r.valid_from > at:
                continue
            if r.valid_until and r.valid_until <= at:
                continue
            result.append(r)
        return result

    def what_changed(self, organization_id: str, since: datetime, subject: str | None = None) -> list[TemporalKnowledgeRecord]:
        prefix = f"{organization_id}:"
        out = [v for k, v in self._store.items() if k.startswith(prefix) and v.created_at >= since]
        if subject:
            out = [r for r in out if r.subject == subject]
        return out

    def evolution(self, organization_id: str, subject: str) -> list[TemporalKnowledgeRecord]:
        prefix = f"{organization_id}:"
        out = [v for k, v in self._store.items() if k.startswith(prefix) and v.subject == subject]
        return sorted(out, key=lambda x: x.valid_from)

    def detect_stale(self, organization_id: str, days: int = 90) -> list[TemporalKnowledgeRecord]:
        from datetime import timedelta
        cutoff = datetime.now(UTC) - timedelta(days=days)
        prefix = f"{organization_id}:"
        return [v for k, v in self._store.items() if k.startswith(prefix) and v.created_at < cutoff and v.status == "active"]

    def detect_duplicates(self, organization_id: str) -> list[dict[str, Any]]:
        prefix = f"{organization_id}:"
        by_content: dict[str, list[TemporalKnowledgeRecord]] = {}
        for k, v in self._store.items():
            if k.startswith(prefix) and v.status == "active":
                by_content.setdefault(v.content, []).append(v)
        return [{"content": c, "ids": [r.record_id for r in lst]} for c, lst in by_content.items() if len(lst) > 1]


__all__ = ["TemporalKnowledgeRecord", "TemporalKnowledgeStore"]
