"""Domain events for event retention management."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from eaip.eventret.models import RetentionAction
from eaip.events.event import DomainEvent


class PolicyCreated(DomainEvent):
    """Emitted when a new retention policy is created."""

    event_type: ClassVar[str] = "eaip.eventret.policy.created"

    policy_id: str
    name: str
    action: RetentionAction
    enabled: bool = Field(default=True)


class PolicyApplied(DomainEvent):
    """Emitted when a retention policy is applied."""

    event_type: ClassVar[str] = "eaip.eventret.policy.applied"

    policy_id: str
    name: str
    affected_events: int = Field(default=0)
    action: RetentionAction


class RetentionJobCompleted(DomainEvent):
    """Emitted when a retention job completes successfully."""

    event_type: ClassVar[str] = "eaip.eventret.job.completed"

    job_id: str
    policy_id: str
    affected_events: int = Field(default=0)
    duration_seconds: float = Field(default=0.0)


class RetentionJobFailed(DomainEvent):
    """Emitted when a retention job fails."""

    event_type: ClassVar[str] = "eaip.eventret.job.failed"

    job_id: str
    policy_id: str
    error_message: str = Field(default="")


__all__ = [
    "PolicyApplied",
    "PolicyCreated",
    "RetentionJobCompleted",
    "RetentionJobFailed",
]
