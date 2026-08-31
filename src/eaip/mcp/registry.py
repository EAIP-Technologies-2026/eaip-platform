from __future__ import annotations

from eaip.mcp.models import MCPServerRecord, MCPServerStatus, MCPToolDefinition
from eaip.shared.time import utc_now


def _key(tenant_id: str, server_id: str) -> str:
    return f"{tenant_id}:{server_id}"


class MCPServerRegistry:
    def __init__(self) -> None:
        self._store: dict[str, MCPServerRecord] = {}

    def register(self, record: MCPServerRecord) -> MCPServerRecord:
        self._store[_key(record.tenant_id, record.server_id)] = record
        return record

    def get(self, server_id: str, tenant_id: str) -> MCPServerRecord | None:
        return self._store.get(_key(tenant_id, server_id))

    def list_for_tenant(self, tenant_id: str) -> list[MCPServerRecord]:
        return [v for k, v in self._store.items() if k.startswith(f"{tenant_id}:")]

    def update(self, server_id: str, tenant_id: str, patch: dict) -> MCPServerRecord | None:
        k = _key(tenant_id, server_id)
        existing = self._store.get(k)
        if not existing:
            return None
        merged = existing.model_dump()
        merged.update(patch)
        merged["updated_at"] = utc_now()
        updated = MCPServerRecord.model_validate(merged)
        self._store[k] = updated
        return updated

    def delete(self, server_id: str, tenant_id: str) -> bool:
        return self._store.pop(_key(tenant_id, server_id), None) is not None

    def set_status(self, server_id: str, tenant_id: str, status: MCPServerStatus) -> MCPServerRecord | None:
        return self.update(server_id, tenant_id, {"status": status})

    def health_summary(self, tenant_id: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for r in self.list_for_tenant(tenant_id):
            counts[r.status.value] = counts.get(r.status.value, 0) + 1
        return counts


class MCPToolRegistry:
    def __init__(self) -> None:
        self._store: dict[str, MCPToolDefinition] = {}

    def _tkey(self, tenant_id: str, server_id: str, name: str) -> str:
        return f"{tenant_id}:{server_id}:{name}"

    def discover(self, server_id: str, tenant_id: str, tools: list[MCPToolDefinition]) -> None:
        to_remove = [k for k in self._store if k.startswith(f"{tenant_id}:{server_id}:")]
        for k in to_remove:
            self._store.pop(k, None)
        for t in tools:
            self._store[self._tkey(t.tenant_id, t.server_id, t.name)] = t

    def list_for_tenant(self, tenant_id: str) -> list[MCPToolDefinition]:
        return [v for k, v in self._store.items() if k.startswith(f"{tenant_id}:")]

    def list_for_server(self, server_id: str, tenant_id: str) -> list[MCPToolDefinition]:
        return [v for k, v in self._store.items() if k.startswith(f"{tenant_id}:{server_id}:")]

    def get(self, server_id: str, tenant_id: str, name: str) -> MCPToolDefinition | None:
        return self._store.get(self._tkey(tenant_id, server_id, name))
