"""Digital Workforce 2.0 models — DigitalEmployee, assignments and capacity.

Extends the existing workforce package without duplicating WorkerDefinition /
WorkerAssignment. All models are frozen Pydantic with tenant isolation and UTC
timestamps via :func:`eaip.shared.time.utc_now`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from eaip.shared.time import utc_now


class DigitalEmployee(BaseModel):
    """Rich digital employee profile for workforce 2.0.

    Attributes:
        employee_id: Stable identifier scoped to tenant.
        tenant_id: Owning tenant / organization.
        name: Display name.
        role: Functional role (e.g. analyst, engineer).
        department: Department or business unit.
        responsibilities: Ordered responsibilities.
        capabilities: High-level capabilities.
        skills: Mapping skill -> proficiency in ``[0, 1]``.
        proficiency: Aggregate proficiency in ``[0, 1]``.
        availability: One of available / busy / offline.
        workload: Current load in ``[0, 1]``.
        goals: Assigned goals / OKRs.
        supervisor: Supervisor employee_id or name.
        permissions: Granted permission strings.
        risk_level: Risk tier (low / medium / high / critical).
        performance: Free-form performance metrics.
        status: Lifecycle status (active / inactive / suspended).
        learning_history: Immutable history of learning events.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    employee_id: str
    tenant_id: str
    name: str
    role: str = ""
    department: str = ""
    responsibilities: tuple[str, ...] = Field(default_factory=tuple)
    capabilities: tuple[str, ...] = Field(default_factory=tuple)
    skills: dict[str, float] = Field(default_factory=dict)
    proficiency: float = Field(default=0.5, ge=0.0, le=1.0)
    availability: str = Field(default="available")
    workload: float = Field(default=0.0, ge=0.0, le=1.0)
    goals: tuple[str, ...] = Field(default_factory=tuple)
    supervisor: str = ""
    permissions: tuple[str, ...] = Field(default_factory=tuple)
    risk_level: str = Field(default="low")
    performance: dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="active")
    learning_history: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("availability")
    @classmethod
    def _validate_availability(cls, v: str) -> str:
        allowed = {"available", "busy", "offline"}
        if v not in allowed:
            raise ValueError(f"availability must be one of {allowed}")
        return v

    @field_validator("skills")
    @classmethod
    def _validate_skills(cls, v: dict[str, float]) -> dict[str, float]:
        for skill, prof in v.items():
            if not isinstance(skill, str) or not skill.strip():
                raise ValueError("skill name must be non-empty string")
            if not isinstance(prof, (int, float)):
                raise ValueError(f"skill {skill!r} proficiency must be numeric")
            if not 0.0 <= float(prof) <= 1.0:
                raise ValueError(f"skill {skill!r} proficiency must be in [0,1]")
        return {k: float(vv) for k, vv in v.items()}

    @field_validator("risk_level")
    @classmethod
    def _validate_risk(cls, v: str) -> str:
        allowed = {"low", "medium", "high", "critical"}
        if v not in allowed:
            # allow custom but normalise lower
            return v.lower()
        return v

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: str) -> str:
        allowed = {"active", "inactive", "suspended", "archived"}
        if v not in allowed:
            return v.lower()
        return v


class WorkforceAssignment2(BaseModel):
    """Workload-aware assignment for Digital Workforce 2.0."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    assignment_id: str
    tenant_id: str
    employee_id: str
    task_id: str = ""
    task_description: str = ""
    task_requirements: dict[str, float] = Field(default_factory=dict)
    status: str = Field(default="pending")
    priority: int = Field(default=0, ge=0, le=10)
    workload_cost: float = Field(default=0.1, ge=0.0, le=1.0)
    assigned_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    result: str = ""
    error: str | None = None

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: str) -> str:
        allowed = {"pending", "assigned", "running", "completed", "failed", "cancelled"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class WorkforceCapacity2(BaseModel):
    """Capacity snapshot for a tenant's digital workforce."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str
    total: int = Field(ge=0)
    available: int = Field(ge=0)
    busy: int = Field(ge=0)
    offline: int = Field(ge=0)
    utilization: float = Field(ge=0.0, le=1.0)
    total_workload: float = Field(default=0.0, ge=0.0)
    available_capacity: float = Field(default=0.0, ge=0.0)
    timestamp: datetime = Field(default_factory=utc_now)


__all__ = ["DigitalEmployee", "WorkforceAssignment2", "WorkforceCapacity2"]
