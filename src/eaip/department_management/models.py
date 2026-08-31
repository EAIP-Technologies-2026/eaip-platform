"""Department domain models — organizational units, members, budgets, resources."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class DepartmentStatus(StrEnum):
    """Lifecycle status of a department."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class DepartmentRole(StrEnum):
    """Role a member can hold within a department."""

    HEAD = "head"
    MANAGER = "manager"
    MEMBER = "member"
    OBSERVER = "observer"


class DepartmentResourceType(StrEnum):
    """Type of resource allocated to a department."""

    BUDGET = "budget"
    EQUIPMENT = "equipment"
    SOFTWARE = "software"
    FACILITY = "facility"
    VEHICLE = "vehicle"
    OTHER = "other"


class Department(BaseModel):
    """A department within the organizational hierarchy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    status: DepartmentStatus = DepartmentStatus.ACTIVE
    parent_id: str | None = None
    category_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DepartmentHierarchy(BaseModel):
    """Represents the hierarchical relationship between departments."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    department_id: str
    ancestor_id: str
    depth: int = Field(ge=0)
    path: list[str] = Field(default_factory=list)


class DepartmentMember(BaseModel):
    """A member belonging to a department."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    department_id: str
    user_id: str
    role: DepartmentRole = DepartmentRole.MEMBER
    joined_at: datetime = Field(default_factory=utc_now)
    is_active: bool = True


class DepartmentSettings(BaseModel):
    """Configuration settings for a department."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    department_id: str
    allow_external_collaboration: bool = False
    max_members: int = 100
    auto_approve_budget: bool = False
    notify_on_changes: bool = True
    settings: dict[str, Any] = Field(default_factory=dict)


class DepartmentPolicy(BaseModel):
    """A policy attached to a department."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    department_id: str
    name: str
    description: str = ""
    rules: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = Field(default_factory=utc_now)


class DepartmentBudget(BaseModel):
    """Budget allocated to a department."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    department_id: str
    fiscal_year: str
    total_amount: float = 0.0
    spent_amount: float = 0.0
    currency: str = "USD"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @property
    def remaining(self) -> float:
        """Return the remaining budget."""
        return self.total_amount - self.spent_amount


class DepartmentResource(BaseModel):
    """A resource allocated to a department."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    department_id: str
    resource_type: DepartmentResourceType
    name: str
    description: str = ""
    quantity: int = 1
    allocated_at: datetime = Field(default_factory=utc_now)
    released_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DepartmentReport(BaseModel):
    """A generated report for a department."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    department_id: str
    report_type: str
    title: str
    data: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=utc_now)
    generated_by: str = "system"


class DepartmentAuditEntry(BaseModel):
    """An audit log entry for department operations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    department_id: str
    action: str
    actor_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    details: dict[str, Any] = Field(default_factory=dict)


class DepartmentConfig(BaseModel):
    """Global configuration for the department management subsystem."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_depth: int = 10
    allow_nested_departments: bool = True
    default_role: DepartmentRole = DepartmentRole.MEMBER
    audit_enabled: bool = True


class DepartmentCategory(BaseModel):
    """A category for classifying departments."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""


class DepartmentContact(BaseModel):
    """Contact information for a department."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    department_id: str
    email: str = ""
    phone: str = ""
    address: str = ""
    primary_contact_id: str | None = None
