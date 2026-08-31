"""Admin domain models — actions, audits, snapshots, and capabilities."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class AuditOutcome(StrEnum):
    """Outcome of an audited operation."""

    SUCCESS = "success"
    FAILURE = "failure"


class AdminAction(BaseModel):
    """A record of an administrative action performed at runtime."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action_id: str
    action_type: str
    target: str
    timestamp: datetime = Field(default_factory=utc_now)
    performed_by: str
    details: dict[str, Any] = Field(default_factory=dict)
    result: str = "pending"


class AuditEntry(BaseModel):
    """An immutable audit trail entry recording a security-relevant event."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    timestamp: datetime = Field(default_factory=utc_now)
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    outcome: AuditOutcome
    correlation_id: str | None = None


class RuntimeSnapshot(BaseModel):
    """A point-in-time snapshot of the runtime environment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    collected_at: datetime = Field(default_factory=utc_now)
    component_states: dict[str, str] = Field(default_factory=dict)
    health_status: str = "unknown"
    active_modules: list[str] = Field(default_factory=list)
    active_capabilities: list[str] = Field(default_factory=list)
    uptime_seconds: float = 0.0


class AdminCapability(BaseModel):
    """Describes an administrative capability exposed by the platform."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    required_role: str = "admin"
    enabled: bool = True
