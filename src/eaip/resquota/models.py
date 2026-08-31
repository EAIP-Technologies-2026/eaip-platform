"""Data models for resource quotas — quotas, allocations, config, and usage."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ResourceQuota(BaseModel):
    """A resource quota definition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    limit: float = Field(default=0, ge=0)
    unit: str = Field(default="")
    allocated: float = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class QuotaAllocation(BaseModel):
    """An allocation of quota to a consumer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    quota_id: str
    amount: float = Field(default=0, ge=0)
    consumer_id: str
    allocated_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = Field(default=None)


class QuotaConfig(BaseModel):
    """Configuration for resource quota enforcement."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    default_limit: float = Field(default=1000, ge=0)
    warn_threshold: float = Field(default=0.8, ge=0, le=1)
    enforce_strict: bool = Field(default=True)
    refresh_interval_seconds: int = Field(default=60, ge=0)


class QuotaUsage(BaseModel):
    """Usage snapshot of a quota for a specific consumer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    quota_id: str
    consumer_id: str
    used: float = Field(default=0, ge=0)
    limit: float = Field(default=0, ge=0)
    percentage: float = Field(default=0, ge=0, le=100)
    last_updated: datetime = Field(default_factory=utc_now)


__all__ = [
    "QuotaAllocation",
    "QuotaConfig",
    "QuotaUsage",
    "ResourceQuota",
]
