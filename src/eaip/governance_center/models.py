"""Governance Command Center models — GovernedSystem, RiskAssessment, PolicyRecord.

Tenant-isolated, immutable (frozen) records for the second governance surface
(prefix /governance2). This complements the existing /governance routes.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class GovernedSystemType(StrEnum):
    """Type discriminator for governed systems."""

    model = "model"
    agent = "agent"
    prompt = "prompt"
    methodology = "methodology"
    connector = "connector"
    capability = "capability"


class RiskLevel(StrEnum):
    """Risk tier for governed systems."""

    low = "low"
    moderate = "moderate"
    high = "high"
    critical = "critical"


class GovernedSystem(BaseModel):
    """Immutable governed system record — tenant-isolated."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    system_id: str
    tenant_id: str
    type: GovernedSystemType = GovernedSystemType.model
    name: str
    version: str = "1.0.0"
    risk: RiskLevel = RiskLevel.low
    owner: str = ""
    lifecycle: str = "draft"
    approval: str = "pending"
    policy_status: str = "pending"
    description: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class RiskAssessment(BaseModel):
    """Result of a risk assessment / risk update on a governed system."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    assessment_id: str
    tenant_id: str
    system_id: str
    risk: RiskLevel
    previous_risk: RiskLevel | None = None
    rationale: str = ""
    assessed_by: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PolicyRecord(BaseModel):
    """Policy governing allowed actions for governed systems."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_id: str
    tenant_id: str
    name: str
    description: str = ""
    allowed_actions: tuple[str, ...] = Field(default_factory=tuple)
    risk_threshold: RiskLevel = RiskLevel.high
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


__all__ = [
    "GovernedSystem",
    "GovernedSystemType",
    "PolicyRecord",
    "RiskAssessment",
    "RiskLevel",
]
