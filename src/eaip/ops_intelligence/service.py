"""OpsIntelligenceService — store, ingest, list, get, escalate."""

from __future__ import annotations

from typing import Any

from eaip.ops_intelligence.detector import InsightDetector
from eaip.ops_intelligence.models import Insight


class OpsIntelligenceService:
    """Tenant-isolated ops intelligence service.

    Store is keyed by ``{tenant_id}:{insight_id}``.
    """

    def __init__(self, detector: InsightDetector | None = None) -> None:
        self.detector = detector or InsightDetector()
        self.store: dict[str, Insight] = {}

    def _key(self, tenant_id: str, insight_id: str) -> str:
        return f"{tenant_id}:{insight_id}"

    def ingest_event(self, event: dict[str, Any]) -> Insight | None:
        tenant_id = str(event.get("tenant_id") or event.get("tenantId") or "default")
        insights = self.detector.detect([event])
        # detector returns tenant-scoped insights; keep only matching tenant
        for ins in insights:
            if ins.tenant_id == tenant_id:
                self.store[self._key(ins.tenant_id, ins.insight_id)] = ins
                return ins
        # no insight
        return None

    def ingest_events(self, events: list[dict[str, Any]]) -> list[Insight]:
        results: list[Insight] = []
        for ins in self.detector.detect(events):
            self.store[self._key(ins.tenant_id, ins.insight_id)] = ins
            results.append(ins)
        return results

    def list_for_tenant(self, tenant_id: str) -> list[Insight]:
        prefix = f"{tenant_id}:"
        return [v for k, v in self.store.items() if k.startswith(prefix)]

    def get(self, insight_id: str, tenant_id: str) -> Insight | None:
        return self.store.get(self._key(tenant_id, insight_id))

    def escalate(self, insight_id: str, tenant_id: str) -> Insight | None:
        cur = self.get(insight_id, tenant_id)
        if cur is None:
            return None
        updated = cur.model_copy(update={"status": "escalated"})
        self.store[self._key(tenant_id, insight_id)] = updated
        return updated

    def acknowledge(self, insight_id: str, tenant_id: str) -> Insight | None:
        cur = self.get(insight_id, tenant_id)
        if cur is None:
            return None
        updated = cur.model_copy(update={"status": "acknowledged"})
        self.store[self._key(tenant_id, insight_id)] = updated
        return updated

    def close(self, insight_id: str, tenant_id: str) -> Insight | None:
        cur = self.get(insight_id, tenant_id)
        if cur is None:
            return None
        updated = cur.model_copy(update={"status": "closed"})
        self.store[self._key(tenant_id, insight_id)] = updated
        return updated


__all__ = ["OpsIntelligenceService"]
