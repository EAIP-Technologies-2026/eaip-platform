"""Data models for floating license management."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class LeaseStatus(StrEnum):
    ACTIVE = "active"
    RETURNED = "returned"
    EXPIRED = "expired"


class LicensePool(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    total_licenses: int = Field(ge=0)
    available_licenses: int = Field(ge=0)
    vendor: str
    product: str
    expiration: datetime | None = Field(default=None)


class LicenseLease(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    pool_id: str
    licensee: str
    checked_out_at: datetime = Field(default_factory=utc_now)
    checked_in_at: datetime | None = Field(default=None)
    status: LeaseStatus = Field(default=LeaseStatus.ACTIVE)


class LicenseConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_lease_duration_minutes: int = Field(default=60, ge=1)
    max_leases_per_licensee: int = Field(default=5, ge=1)
    enable_auto_release: bool = Field(default=True)
    grace_period_seconds: int = Field(default=30, ge=0)


__all__ = [
    "LeaseStatus",
    "LicenseConfig",
    "LicenseLease",
    "LicensePool",
]
