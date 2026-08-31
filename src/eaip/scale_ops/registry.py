"""M8 registries — tenant-isolated."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any

from eaip.scale_ops.models import (
    CapacityForecast,
    DataResidencyPolicy,
    DeploymentCapabilityProfile,
    DeploymentProfile,
    DisasterRecoveryPoint,
    HealthSignal,
    IncidentRecord,
    RegionInfo,
    RuntimePool,
    WorkloadItem,
    WorkloadPriority,
)


class PoolRegistry:
    def __init__(self) -> None:
        self._pools: dict[str, RuntimePool] = {}

    def create(self, pool: RuntimePool) -> RuntimePool:
        self._pools[pool.pool_id] = pool
        return pool

    def get(self, pool_id: str, tenant_id: str) -> RuntimePool | None:
        p = self._pools.get(pool_id)
        if p and p.tenant_id == tenant_id:
            return p
        return None

    def list_for_tenant(self, tenant_id: str) -> list[RuntimePool]:
        return [v for v in self._pools.values() if v.tenant_id == tenant_id]

    def delete(self, pool_id: str, tenant_id: str) -> bool:
        p = self._pools.get(pool_id)
        if p and p.tenant_id == tenant_id:
            del self._pools[pool_id]
            return True
        return False


class WorkloadScheduler:
    def __init__(self) -> None:
        self._queue: dict[str, WorkloadItem] = {}

    def enqueue(self, item: WorkloadItem) -> WorkloadItem:
        self._queue[item.workload_id] = item
        return item

    def schedule(self, tenant_id: str, available_runtimes: list[dict[str, Any]] | None = None) -> WorkloadItem | None:
        candidates = [v for v in self._queue.values() if v.tenant_id == tenant_id and v.status == "queued"]
        if not candidates:
            return None
        # priority order
        order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
        candidates.sort(key=lambda x: order.get(x.priority.value, 2))
        chosen = candidates[0]
        # capability matching
        if available_runtimes:
            for rt in available_runtimes:
                caps = rt.get("capabilities", [])
                if not chosen.required_capabilities or any(c in caps for c in chosen.required_capabilities):
                    chosen.status = "scheduled"
                    chosen.assigned_runtime = rt.get("runtime_id", "")
                    return chosen
        chosen.status = "scheduled"
        return chosen

    def list_for_tenant(self, tenant_id: str) -> list[WorkloadItem]:
        return [v for v in self._queue.values() if v.tenant_id == tenant_id]

    def get(self, workload_id: str, tenant_id: str) -> WorkloadItem | None:
        w = self._queue.get(workload_id)
        if w and w.tenant_id == tenant_id:
            return w
        return None


class RegionRegistry:
    def __init__(self) -> None:
        self._regions: dict[str, RegionInfo] = {}

    def register(self, region: RegionInfo) -> RegionInfo:
        self._regions[region.region] = region
        return region

    def get(self, region: str) -> RegionInfo | None:
        return self._regions.get(region)

    def list_all(self) -> list[RegionInfo]:
        return list(self._regions.values())


class DataResidencyRegistry:
    def __init__(self) -> None:
        self._policies: dict[str, DataResidencyPolicy] = {}

    def create(self, policy: DataResidencyPolicy) -> DataResidencyPolicy:
        self._policies[policy.policy_id] = policy
        return policy

    def check(self, tenant_id: str, data_class: str, region: str, model: str = "", connector: str = "") -> dict[str, Any]:
        for p in self._policies.values():
            if p.tenant_id == tenant_id and p.data_class == data_class:
                if p.allowed_regions and region not in p.allowed_regions:
                    return {"allowed": False, "reason": f"region {region} not allowed for {data_class}"}
                if p.allowed_models and model and model not in p.allowed_models:
                    return {"allowed": False, "reason": f"model {model} not allowed for {data_class}"}
                if p.allowed_connectors and connector and connector not in p.allowed_connectors:
                    return {"allowed": False, "reason": f"connector {connector} not allowed for {data_class}"}
        return {"allowed": True}

    def list_for_tenant(self, tenant_id: str) -> list[DataResidencyPolicy]:
        return [v for v in self._policies.values() if v.tenant_id == tenant_id]


class IncidentRegistry:
    def __init__(self) -> None:
        self._incidents: dict[str, IncidentRecord] = {}

    def create(self, incident: IncidentRecord) -> IncidentRecord:
        self._incidents[incident.incident_id] = incident
        return incident

    def get(self, incident_id: str, tenant_id: str) -> IncidentRecord | None:
        inc = self._incidents.get(incident_id)
        if inc and inc.tenant_id == tenant_id:
            return inc
        return None

    def list_for_tenant(self, tenant_id: str) -> list[IncidentRecord]:
        return [v for v in self._incidents.values() if v.tenant_id == tenant_id]

    def correlate(self, tenant_id: str, incident_ids: list[str]) -> IncidentRecord | None:
        incidents = [self._incidents.get(i) for i in incident_ids if self._incidents.get(i) and self._incidents.get(i).tenant_id == tenant_id]  # type: ignore[union-attr]
        if not incidents:
            return None
        primary = incidents[0]
        primary.correlated_ids = [i.incident_id for i in incidents[1:]]
        primary.diagnosis = f"Correlated {len(incidents)} incidents: {', '.join(i.title for i in incidents)}"
        return primary

    def remediate(self, incident_id: str, tenant_id: str, action: str) -> IncidentRecord | None:
        inc = self.get(incident_id, tenant_id)
        if not inc:
            return None
        inc.remediation = action
        inc.status = "remediated"
        inc.updated_at = datetime.now(UTC)
        return inc


class DisasterRecoveryRegistry:
    def __init__(self) -> None:
        self._points: dict[str, DisasterRecoveryPoint] = {}

    def create_point(self, tenant_id: str) -> DisasterRecoveryPoint:
        pt = DisasterRecoveryPoint(tenant_id=tenant_id, state_hash=hashlib.sha256(f"{tenant_id}:{datetime.now(UTC).isoformat()}".encode()).hexdigest()[:16])
        self._points[pt.point_id] = pt
        return pt

    def list_for_tenant(self, tenant_id: str) -> list[DisasterRecoveryPoint]:
        return [v for v in self._points.values() if v.tenant_id == tenant_id]


DEPLOYMENT_PROFILES: dict[str, dict[str, Any]] = {
    "cloud": {"human_requirements": ["cloud account", "DNS/TLS"], "description": "Fully managed cloud deployment"},
    "private_cloud": {"human_requirements": ["private cloud infra", "VPC", "IdP"], "description": "Private cloud with tenant isolation"},
    "on_premise": {"human_requirements": ["on-prem hardware", "network", "IdP", "vault", "backup infra"], "description": "On-premise deployment"},
    "hybrid": {"human_requirements": ["cloud + on-prem bridge", "network peering"], "description": "Hybrid cloud/on-prem"},
    "air_gapped": {"human_requirements": ["air-gapped network", "offline model registry", "manual artifact transfer"], "description": "Air-gapped isolated deployment"},
}
