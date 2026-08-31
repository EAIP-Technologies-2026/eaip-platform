"""M8 Enterprise Scale + Production Operations models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PoolKind(str, Enum):
    general = "general"
    gpu = "gpu"
    high_memory = "high_memory"
    isolated = "isolated"


class RuntimePool(BaseModel):
    pool_id: str = Field(default_factory=lambda: f"pool-{uuid.uuid4().hex[:8]}")
    name: str
    kind: PoolKind = PoolKind.general
    capacity: int = 10
    region: str = "us-east-1"
    tenant_id: str = "default"
    runtimes: list[str] = Field(default_factory=list)
    status: str = "healthy"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WorkloadPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    critical = "critical"


class WorkloadItem(BaseModel):
    workload_id: str = Field(default_factory=lambda: f"wl-{uuid.uuid4().hex[:8]}")
    tenant_id: str
    priority: WorkloadPriority = WorkloadPriority.normal
    workload_type: str = "general"
    payload: dict[str, Any] = Field(default_factory=dict)
    required_capabilities: list[str] = Field(default_factory=list)
    region: str = "us-east-1"
    status: str = "queued"
    assigned_runtime: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HealthSignal(BaseModel):
    component: str
    status: str = "healthy"
    latency_ms: float = 0
    error_rate: float = 0
    details: dict[str, Any] = Field(default_factory=dict)


class RegionInfo(BaseModel):
    region: str
    deployment: str = "primary"
    runtimes: list[str] = Field(default_factory=list)
    data_locality: str = "us-east-1"
    status: str = "active"


class DataResidencyPolicy(BaseModel):
    policy_id: str = Field(default_factory=lambda: f"drp-{uuid.uuid4().hex[:8]}")
    tenant_id: str
    data_class: str = "general"
    allowed_regions: list[str] = Field(default_factory=list)
    allowed_models: list[str] = Field(default_factory=list)
    allowed_connectors: list[str] = Field(default_factory=list)
    allowed_storage: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DeploymentProfile(str, Enum):
    cloud = "cloud"
    private_cloud = "private_cloud"
    on_premise = "on_premise"
    hybrid = "hybrid"
    air_gapped = "air_gapped"


class DeploymentCapabilityProfile(BaseModel):
    profile: DeploymentProfile = DeploymentProfile.cloud
    human_requirements: list[str] = Field(default_factory=list)
    description: str = ""


class IncidentRecord(BaseModel):
    incident_id: str = Field(default_factory=lambda: f"inc-{uuid.uuid4().hex[:8]}")
    tenant_id: str
    title: str
    severity: str = "medium"
    status: str = "open"
    correlated_ids: list[str] = Field(default_factory=list)
    diagnosis: str = ""
    recommendations: list[str] = Field(default_factory=list)
    remediation: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CapacityForecast(BaseModel):
    resource: str
    current: float = 0
    predicted: float = 0
    growth_rate: float = 0
    forecast_days: int = 7
    recommendation: str = ""


class DisasterRecoveryPoint(BaseModel):
    point_id: str = Field(default_factory=lambda: f"drp-{uuid.uuid4().hex[:8]}")
    tenant_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    state_hash: str = ""
    recovery_objective: str = ""
    validated: bool = False
