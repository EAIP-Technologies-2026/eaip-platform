from __future__ import annotations

from typing import Any

from eaip.intelligence.models import CapabilityHealth, CapabilityRecord, CapabilityStatus


class CapabilityRegistry:
    def __init__(self) -> None:
        self._store: dict[str, CapabilityRecord] = {}
        self._health: dict[str, CapabilityHealth] = {}

    def _key(self, tenant_id: str, capability_id: str) -> str:
        return f"{tenant_id}:{capability_id}"

    def register(self, record: CapabilityRecord) -> CapabilityRecord:
        self._store[self._key(record.tenant_id, record.capability_id)] = record
        self._health[self._key(record.tenant_id, record.capability_id)] = CapabilityHealth(capability_id=record.capability_id, status=record.health)
        return record

    def get(self, capability_id: str, tenant_id: str) -> CapabilityRecord | None:
        return self._store.get(self._key(tenant_id, capability_id))

    def list_for_tenant(self, tenant_id: str) -> list[CapabilityRecord]:
        return [v for k, v in self._store.items() if k.startswith(f"{tenant_id}:")]

    def search(self, tenant_id: str, query: str = "", category: str = "") -> list[CapabilityRecord]:
        results = self.list_for_tenant(tenant_id)
        if query:
            q = query.lower()
            results = [r for r in results if q in r.name.lower() or q in r.description.lower()]
        if category:
            results = [r for r in results if r.category.value == category]
        return results

    def health(self, capability_id: str, tenant_id: str) -> CapabilityHealth | None:
        return self._health.get(self._key(tenant_id, capability_id))

    def update_availability(self, capability_id: str, tenant_id: str, availability: float) -> None:
        k = self._key(tenant_id, capability_id)
        h = self._health.get(k)
        if h:
            self._health[k] = h.model_copy(update={"availability": availability})

    def set_status(self, capability_id: str, tenant_id: str, status: CapabilityStatus) -> None:
        k = self._key(tenant_id, capability_id)
        rec = self._store.get(k)
        if rec:
            self._store[k] = rec.model_copy(update={"health": status})
        h = self._health.get(k)
        if h:
            self._health[k] = h.model_copy(update={"status": status})
