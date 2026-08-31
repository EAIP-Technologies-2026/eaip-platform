from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class AutonomyLevel(StrEnum):
    L0_OBSERVE = "L0"
    L1_RECOMMEND = "L1"
    L2_REVERSIBLE = "L2"
    L3_APPROVED = "L3"
    L4_BOUNDED = "L4"


class AutonomyDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class AutonomyPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_id: str
    tenant_id: str
    name: str
    max_level: AutonomyLevel = AutonomyLevel.L1_RECOMMEND
    allowed_tools: tuple[str, ...] = Field(default_factory=tuple)
    blocked_tools: tuple[str, ...] = Field(default_factory=tuple)
    allowed_connectors: tuple[str, ...] = Field(default_factory=tuple)
    max_budget: float = 1000.0
    max_time_s: float = 300.0
    require_approval_for: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = ["AutonomyDecision", "AutonomyLevel", "AutonomyPolicy"]
