from __future__ import annotations

from eaip.runtime_registry.models import RuntimeRecord, RuntimeStatus


class RuntimeRegistry:
    def __init__(self) -> None:
        self._store: dict[str, RuntimeRecord] = {}

    def _key(self, runtime_id: str) -> str:
        return runtime_id

    def register(self, record: RuntimeRecord) -> RuntimeRecord:
        self._store[self._key(record.runtime_id)] = record
        return record

    def get(self, runtime_id: str) -> RuntimeRecord | None:
        return self._store.get(self._key(runtime_id))

    def list_all(self) -> list[RuntimeRecord]:
        return list(self._store.values())

    def list_for_tenant(self, tenant_id: str) -> list[RuntimeRecord]:
        return [v for v in self._store.values() if v.tenant_id in (tenant_id, "default")]

    def set_status(self, runtime_id: str, status: RuntimeStatus) -> RuntimeRecord | None:
        rec = self._store.get(self._key(runtime_id))
        if not rec:
            return None
        updated = rec.model_copy(update={"status": status})
        self._store[self._key(runtime_id)] = updated
        return updated

    def delete(self, runtime_id: str) -> bool:
        return self._store.pop(self._key(runtime_id), None) is not None

    def schedule(self, required_capabilities: list[str] | None = None, tenant_id: str = "default") -> dict[str, Any] | None:
        candidates = [r for r in self.list_for_tenant(tenant_id) if r.status.value == "healthy"]
        if required_capabilities:
            scored = []
            for r in candidates:
                match = len(set(required_capabilities) & set(r.capabilities))
                scored.append((match, r))
            scored.sort(key=lambda x: x[0], reverse=True)
            candidates = [r for _, r in scored if _[0] > 0] or candidates
        if not candidates:
            return None
        chosen = candidates[0]
        return chosen.model_dump(mode="json")

    def failover(self, failed_runtime_id: str, tenant_id: str = "default") -> dict[str, Any] | None:
        failed = self.get(failed_runtime_id)
        if not failed:
            return None
        self.set_status(failed_runtime_id, __import__("eaip.runtime_registry.models", fromlist=["RuntimeStatus"]).RuntimeStatus.offline)
        return self.schedule(list(failed.capabilities), tenant_id=tenant_id)
