"""DigitalTwin — enterprise digital twin model and registry.

Tenant-isolated. Each twin belongs to exactly one tenant_id.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class DigitalTwin(BaseModel):
    """Enterprise digital twin snapshot.

    Covers workforce, agents, processes, resources, suppliers,
    customers, inventory, schedules, financials, KPIs, and risk.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    twin_id: str = Field(description="Unique twin identifier")
    tenant_id: str = Field(description="Owning tenant")
    enterprise: str = Field(default="apex", description="apex | nova | meridian")
    state: dict[str, Any] = Field(default_factory=dict)
    workforce: dict[str, Any] = Field(default_factory=dict)
    agents: dict[str, Any] = Field(default_factory=dict)
    processes: dict[str, Any] = Field(default_factory=dict)
    resources: dict[str, Any] = Field(default_factory=dict)
    suppliers: dict[str, Any] = Field(default_factory=dict)
    customers: dict[str, Any] = Field(default_factory=dict)
    inventory: dict[str, Any] = Field(default_factory=dict)
    schedules: dict[str, Any] = Field(default_factory=dict)
    financial: dict[str, Any] = Field(default_factory=dict)
    kpis: dict[str, Any] = Field(default_factory=dict)
    risk: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class TwinRegistry:
    """Tenant-isolated in-memory registry of DigitalTwins.

    Keyed by ``{tenant_id}:{twin_id}`` to guarantee isolation.
    """

    def __init__(self) -> None:
        self._store: dict[str, DigitalTwin] = {}

    def _key(self, tenant_id: str, twin_id: str) -> str:
        return f"{tenant_id}:{twin_id}"

    def create(
        self,
        tenant_id: str,
        enterprise: str = "apex",
        state: dict[str, Any] | None = None,
        workforce: dict[str, Any] | None = None,
        agents: dict[str, Any] | None = None,
        processes: dict[str, Any] | None = None,
        resources: dict[str, Any] | None = None,
        suppliers: dict[str, Any] | None = None,
        customers: dict[str, Any] | None = None,
        inventory: dict[str, Any] | None = None,
        schedules: dict[str, Any] | None = None,
        financial: dict[str, Any] | None = None,
        kpis: dict[str, Any] | None = None,
        risk: dict[str, Any] | None = None,
        twin_id: str | None = None,
        **extra: Any,
    ) -> DigitalTwin:
        tid = twin_id or f"twin-{uuid.uuid4().hex[:8]}"
        twin = DigitalTwin(
            twin_id=tid,
            tenant_id=tenant_id,
            enterprise=enterprise,
            state=state or extra.get("state") or {},
            workforce=workforce or {},
            agents=agents or {},
            processes=processes or {},
            resources=resources or {},
            suppliers=suppliers or {},
            customers=customers or {},
            inventory=inventory or {},
            schedules=schedules or {},
            financial=financial or {},
            kpis=kpis or {},
            risk=risk or {},
        )
        self._store[self._key(tenant_id, tid)] = twin
        return twin

    def get(self, twin_id: str, tenant_id: str) -> DigitalTwin | None:
        return self._store.get(self._key(tenant_id, twin_id))

    def list_for_tenant(self, tenant_id: str) -> list[DigitalTwin]:
        prefix = f"{tenant_id}:"
        return [v for k, v in self._store.items() if k.startswith(prefix)]

    def update(self, twin_id: str, tenant_id: str, patches: dict[str, Any]) -> DigitalTwin | None:
        cur = self.get(twin_id, tenant_id)
        if cur is None:
            return None
        # Only allow known fields
        allowed = {"state", "workforce", "agents", "processes", "resources", "suppliers", "customers", "inventory", "schedules", "financial", "kpis", "risk", "enterprise"}
        filtered = {k: v for k, v in patches.items() if k in allowed}
        filtered["updated_at"] = utc_now()
        updated = cur.model_copy(update=filtered)
        self._store[self._key(tenant_id, twin_id)] = updated
        return updated

    def delete(self, twin_id: str, tenant_id: str) -> bool:
        key = self._key(tenant_id, twin_id)
        if key in self._store:
            del self._store[key]
            return True
        return False


# Backwards-compatible dict alias for spec: TwinRegistry dict
# Keep a module-level singleton for router fallback
twin_registry = TwinRegistry()

__all__ = ["DigitalTwin", "TwinRegistry", "twin_registry"]
