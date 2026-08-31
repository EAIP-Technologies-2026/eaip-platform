"""Data models for multi-cloud resource management."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ProviderType(StrEnum):
    """Types of cloud providers."""

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    OCI = "oci"
    ALIBABA = "alibaba"


class ResourceStatus(StrEnum):
    """Status of a cloud resource."""

    RUNNING = "running"
    STOPPED = "stopped"
    TERMINATED = "terminated"
    PROVISIONING = "provisioning"
    UNKNOWN = "unknown"


class CloudProvider(BaseModel):
    """A registered cloud provider."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    provider_type: ProviderType
    region: str = Field(default="")
    enabled: bool = Field(default=True)
    credentials_ref: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class CloudResource(BaseModel):
    """A discovered cloud resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    provider_id: str
    resource_type: str
    name: str = Field(default="")
    region: str = Field(default="")
    status: ResourceStatus = Field(default=ResourceStatus.UNKNOWN)
    cost_per_hour: float = Field(default=0.0, ge=0.0)
    tags: dict[str, str] = Field(default_factory=dict)
    discovered_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CostEstimate(BaseModel):
    """A cost estimate comparing resources across providers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    resource_type: str
    estimates: dict[str, float]
    currency: str = Field(default="USD")
    period_hours: int = Field(default=1, ge=1)
    calculated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CloudConfig(BaseModel):
    """Configuration for the cloud resource manager."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    discovery_interval_seconds: int = Field(default=3600, ge=60)
    cost_comparison_enabled: bool = Field(default=True)
    default_region: str = Field(default="us-east-1")
    max_resources_per_provider: int = Field(default=5000, ge=1)
    cache_ttl_seconds: int = Field(default=300, ge=0)


__all__ = [
    "CloudConfig",
    "CloudProvider",
    "CloudResource",
    "CostEstimate",
    "ProviderType",
    "ResourceStatus",
]
