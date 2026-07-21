"""Organization domain models — orgs, units, members, policies, domains, and reports."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class OrganizationStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class OrganizationType(StrEnum):
    CORPORATION = "corporation"
    NONPROFIT = "nonprofit"
    GOVERNMENT = "government"
    EDUCATIONAL = "educational"
    PARTNERSHIP = "partnership"
    SOLE_PROPRIETORSHIP = "sole_proprietorship"
    OTHER = "other"


class OrganizationRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"


class OrganizationUnitType(StrEnum):
    DEPARTMENT = "department"
    DIVISION = "division"
    TEAM = "team"
    PROJECT = "project"
    REGION = "region"
    OTHER = "other"


class Organization(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    slug: str
    status: OrganizationStatus = OrganizationStatus.ACTIVE
    org_type: OrganizationType = OrganizationType.OTHER
    description: str = ""
    domain: str = ""
    parent_org_id: str | None = None
    settings: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class OrganizationHierarchy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    org_id: str
    ancestor_ids: tuple[str, ...] = Field(default=())
    descendant_ids: tuple[str, ...] = Field(default=())
    depth: int = 0
    path: tuple[str, ...] = Field(default=())


class OrganizationUnit(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    org_id: str
    name: str
    unit_type: OrganizationUnitType = OrganizationUnitType.OTHER
    parent_unit_id: str | None = None
    description: str = ""
    head_user_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class OrganizationMember(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    org_id: str
    user_id: str
    email: str
    name: str = ""
    role: OrganizationRole = OrganizationRole.MEMBER
    unit_ids: tuple[str, ...] = Field(default=())
    permissions: tuple[str, ...] = Field(default=())
    joined_at: datetime = Field(default_factory=utc_now)
    last_active: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OrganizationSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    org_id: str
    allow_external_members: bool = False
    require_2fa: bool = False
    max_members: int = 100
    max_units: int = 50
    default_member_role: OrganizationRole = OrganizationRole.MEMBER
    allowed_domains: tuple[str, ...] = Field(default=())
    notification_channels: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=utc_now)


class OrganizationPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    org_id: str
    name: str
    description: str = ""
    policy_type: str
    rules: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    priority: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class OrganizationAuditEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    org_id: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)
    correlation_id: str | None = None


class OrganizationReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    org_id: str
    report_type: str
    generated_at: datetime = Field(default_factory=utc_now)
    period_start: datetime
    period_end: datetime
    total_members: int = 0
    total_units: int = 0
    total_policies: int = 0
    metrics: dict[str, Any] = Field(default_factory=dict)
    data: dict[str, Any] = Field(default_factory=dict)


class OrganizationConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    org_id: str
    key: str
    value: str = ""
    description: str = ""
    updated_at: datetime = Field(default_factory=utc_now)


class OrganizationSubscription(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    org_id: str
    plan: str
    status: str = "active"
    start_date: datetime
    end_date: datetime | None = None
    auto_renew: bool = True
    features: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=utc_now)


class OrganizationFeature(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    org_id: str
    feature_key: str
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=utc_now)


class OrganizationDomain(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    org_id: str
    domain: str
    verified: bool = False
    verification_token: str = ""
    verified_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)


class OrganizationContact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    org_id: str
    name: str = ""
    email: str
    phone: str = ""
    title: str = ""
    is_primary: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
