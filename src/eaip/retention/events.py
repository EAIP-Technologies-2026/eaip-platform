"""Domain events for the data retention and purge service."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class PolicyCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.retention.policy.created"

    policy_id: str
    name: str


class PolicyUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.retention.policy.updated"

    policy_id: str
    changes: dict[str, Any]


class PolicyDeleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.retention.policy.deleted"

    policy_id: str


class PurgeExecuted(DomainEvent):
    event_type: ClassVar[str] = "eaip.retention.purge.executed"

    job_id: str
    policy_id: str
    status: str


__all__ = [
    "PolicyCreated",
    "PolicyDeleted",
    "PolicyUpdated",
    "PurgeExecuted",
]
