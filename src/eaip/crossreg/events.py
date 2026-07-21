"""Domain events for the cross-region replicator."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class ReplicationStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.crossreg.replication.started"

    rule_id: str
    name: str
    source_region: str
    target_region: str


class ReplicationCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.crossreg.replication.completed"

    rule_id: str
    items_synced: int
    items_failed: int
    duration_seconds: float | None = None


class ReplicationFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.crossreg.replication.failed"

    rule_id: str
    error: str
    items_failed: int = Field(default=0)
    details: dict[str, Any] = Field(default_factory=dict)
