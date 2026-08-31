"""Tenant domain models — tenants, users, quotas, config, billing, and reports."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class TenantStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CLOSED = "closed"


class TenantPlan(StrEnum):
    FREE = "free"
    BASIC = "basic"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class TenantUserStatus(StrEnum):
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"
    DISABLED = "disabled"


class BillingStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BillingCategory(StrEnum):
    SUBSCRIPTION = "subscription"
    USAGE = "usage"
    SUPPORT = "support"
    OTHER = "other"


class ConfigValueType(StrEnum):
    STRING = "string"
    INT = "int"
    BOOL = "bool"
    JSON = "json"


class Tenant(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    slug: str
    domain: str = ""
    status: TenantStatus = TenantStatus.ACTIVE
    plan: TenantPlan = TenantPlan.FREE
    settings: dict[str, Any] = Field(default_factory=dict)
    features: tuple[str, ...] = Field(default=())
    quotas: dict[str, int] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)
    contact_email: str = ""
    max_users: int = 10
    max_agents: int = 5
    max_workflows: int = 10
    storage_limit_bytes: int = 1073741824


class TenantUser(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    email: str
    name: str = ""
    roles: tuple[str, ...] = Field(default=())
    status: TenantUserStatus = TenantUserStatus.ACTIVE
    permissions: tuple[str, ...] = Field(default=())
    created_at: datetime = Field(default_factory=utc_now)
    last_login: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TenantQuota(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str
    resource_type: str
    hard_limit: int
    soft_limit: int
    current_usage: int = 0
    remaining: int = 0
    last_updated: datetime = Field(default_factory=utc_now)


class TenantConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    category: str
    key: str
    value: str = ""
    type: ConfigValueType = ConfigValueType.STRING
    description: str = ""
    updated_at: datetime = Field(default_factory=utc_now)


class BillingLineItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    description: str
    quantity: int = 1
    unit_price: float = 0.0
    total: float = 0.0
    category: BillingCategory = BillingCategory.OTHER
    metadata: dict[str, Any] = Field(default_factory=dict)


class BillingRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    period_start: datetime
    period_end: datetime
    amount: float = 0.0
    currency: str = "USD"
    status: BillingStatus = BillingStatus.PENDING
    items: tuple[BillingLineItem, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)


class CrossTenantReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    generated_at: datetime = Field(default_factory=utc_now)
    period_start: datetime
    period_end: datetime
    total_tenants: int = 0
    active_tenants: int = 0
    total_users: int = 0
    total_agents: int = 0
    total_workflows: int = 0
    revenue_total: float = 0.0
    revenue_by_plan: dict[str, float] = Field(default_factory=dict)
    usage_metrics: dict[str, Any] = Field(default_factory=dict)
