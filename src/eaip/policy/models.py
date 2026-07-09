"""Policy model — Policy, PolicyRule, PolicyEffect, PolicyDecision."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class PolicyEffect(StrEnum):
    """Effect of a policy rule on a request."""

    ALLOW = "allow"
    DENY = "deny"


class ConditionOp(StrEnum):
    """ABAC condition operators."""

    EQ = "eq"
    NEQ = "neq"
    IN = "in"
    NOT_IN = "not_in"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    EXISTS = "exists"
    MATCHES = "matches"


class PolicyCondition(BaseModel):
    """An ABAC condition that must be satisfied for a rule to match."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    attribute: str
    operator: ConditionOp
    value: Any = None


class PolicyRule(BaseModel):
    """A single policy rule with RBAC and ABAC matching."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    effect: PolicyEffect
    subjects: tuple[str, ...] = ()
    actions: tuple[str, ...] = ()
    resources: tuple[str, ...] = ()
    conditions: tuple[PolicyCondition, ...] = ()
    priority: int = 0
    description: str = ""


class Policy(BaseModel):
    """A named collection of policy rules."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    rules: tuple[PolicyRule, ...] = ()
    enabled: bool = True
    metadata: dict[str, str] = {}


class PolicyDecision(BaseModel):
    """Result of a policy evaluation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    effect: PolicyEffect
    matched_rules: tuple[str, ...] = ()
    context_snapshot: dict[str, Any] = Field(default_factory=dict)
    explanation: str = ""
    evaluated_at: datetime = Field(default_factory=utc_now)


__all__ = [
    "ConditionOp",
    "Policy",
    "PolicyCondition",
    "PolicyDecision",
    "PolicyEffect",
    "PolicyRule",
]
