"""Policy domain events — emitted during policy evaluation."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class PolicyEvaluated(DomainEvent):
    """Published after every policy evaluation."""

    event_type: ClassVar[str] = "eaip.policy.evaluated"

    subject_id: str
    action: str
    resource: str
    effect: str
    matched_rules: tuple[str, ...] = ()
    context_snapshot: dict[str, Any] = Field(default_factory=dict)


class PolicyViolation(DomainEvent):
    """Published when a request is explicitly denied by policy."""

    event_type: ClassVar[str] = "eaip.policy.violation"

    subject_id: str
    action: str
    resource: str
    matched_rules: tuple[str, ...] = ()
    explanation: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)


class PolicyRuleMatched(DomainEvent):
    """Published when a specific rule matches a request."""

    event_type: ClassVar[str] = "eaip.policy.rule_matched"

    rule_id: str
    rule_name: str
    effect: str
    subject_id: str
    action: str
    resource: str


__all__ = ["PolicyEvaluated", "PolicyRuleMatched", "PolicyViolation"]
