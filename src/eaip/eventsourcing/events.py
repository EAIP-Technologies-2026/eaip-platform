"""Domain events published by the event sourcing subsystem."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class EventStored(DomainEvent):
    event_type: ClassVar[str] = "eventsourcing.event.stored"
    aggregate_type: str
    aggregate_id: str
    event_type_name: str
    version: int


class ProjectionRegistered(DomainEvent):
    event_type: ClassVar[str] = "eventsourcing.projection.registered"
    projection_id: str
    projection_name: str
    aggregate_types: tuple[str, ...] = ()


class ProjectionBuilt(DomainEvent):
    event_type: ClassVar[str] = "eventsourcing.projection.built"
    projection_id: str
    projection_name: str
    events_processed: int


class ProjectionRebuilt(DomainEvent):
    event_type: ClassVar[str] = "eventsourcing.projection.rebuilt"
    projection_id: str
    projection_name: str
    events_processed: int


class ReplayStarted(DomainEvent):
    event_type: ClassVar[str] = "eventsourcing.replay.started"
    aggregate_type: str | None = None
    aggregate_id: str | None = None
    event_type_name: str | None = None
    range_start: int | None = None
    range_end: int | None = None


class ReplayCompleted(DomainEvent):
    event_type: ClassVar[str] = "eventsourcing.replay.completed"
    aggregate_type: str | None = None
    aggregate_id: str | None = None
    event_type_name: str | None = None
    range_start: int | None = None
    range_end: int | None = None
    events_processed: int
    duration_seconds: float


class SnapshotCreated(DomainEvent):
    event_type: ClassVar[str] = "eventsourcing.snapshot.created"
    aggregate_type: str
    aggregate_id: str
    version: int


__all__ = [
    "EventStored",
    "ProjectionBuilt",
    "ProjectionRebuilt",
    "ProjectionRegistered",
    "ReplayCompleted",
    "ReplayStarted",
    "SnapshotCreated",
]
