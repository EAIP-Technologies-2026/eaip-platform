"""Domain events for the masking policy module."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class PolicyCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.maskpolicy.policy.created"
    policy_id: str
    policy_name: str
    environment: str


class PolicyUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.maskpolicy.policy.updated"
    policy_id: str
    policy_name: str
    changes: dict[str, Any] = Field(default_factory=dict)


class PolicyApplied(DomainEvent):
    event_type: ClassVar[str] = "eaip.maskpolicy.policy.applied"
    policy_id: str
    policy_name: str
    rules_applied: int = Field(default=0)


__all__ = [
    "PolicyApplied",
    "PolicyCreated",
    "PolicyUpdated",
]
