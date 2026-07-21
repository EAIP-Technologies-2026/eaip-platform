"""Data models for license & entitlement management."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class LicenseType(StrEnum):
    TRIAL = "trial"
    SUBSCRIPTION = "subscription"
    PERPETUAL = "perpetual"
    USAGE_BASED = "usage_based"


class LicenseStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class License(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    key: str
    type: LicenseType = Field(default=LicenseType.TRIAL)
    status: LicenseStatus = Field(default=LicenseStatus.ACTIVE)
    features: tuple[str, ...] = Field(default=())
    max_users: int = Field(default=0)
    max_agents: int = Field(default=0)
    max_workflows: int = Field(default=0)
    max_storage_bytes: int = Field(default=0)
    issued_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = Field(default=None)
    last_validated_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)
    customer_info: dict[str, Any] = Field(default_factory=dict)


class FeatureEntitlement(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    license_id: str
    feature_key: str
    enabled: bool = Field(default=True)
    limits: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UsageRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    license_id: str
    feature_key: str
    metric: str
    quantity: int = Field(default=1, ge=1)
    timestamp: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LicenseValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    license_id: str
    valid: bool
    errors: tuple[str, ...] = Field(default=())
    warnings: tuple[str, ...] = Field(default=())
    features_available: tuple[str, ...] = Field(default=())
    features_blocked: tuple[str, ...] = Field(default=())
    expires_in_days: int | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LicenseConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    enable_offline_validation: bool = Field(default=True)
    validation_interval_hours: int = Field(default=24, ge=1)
    grace_period_days: int = Field(default=7, ge=0)
    enable_usage_tracking: bool = Field(default=True)
    enable_enforcement: bool = Field(default=True)
    default_license_type: LicenseType = Field(default=LicenseType.TRIAL)


__all__ = [
    "FeatureEntitlement",
    "License",
    "LicenseConfig",
    "LicenseStatus",
    "LicenseType",
    "LicenseValidationResult",
    "UsageRecord",
]
