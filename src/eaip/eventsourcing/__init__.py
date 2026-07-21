"""Event Sourcing — event store, event replay, projection building, and CQRS support."""

from __future__ import annotations

from eaip.eventsourcing.events import (
    EventStored,
    ProjectionBuilt,
    ProjectionRebuilt,
    ProjectionRegistered,
    ReplayCompleted,
    ReplayStarted,
    SnapshotCreated,
)
from eaip.eventsourcing.exceptions import (
    ConcurrencyError,
    EventSourcingError,
    EventStoreError,
    ProjectionNotFoundError,
    ReplayError,
    SnapshotNotFoundError,
)
from eaip.eventsourcing.health import EventSourcingHealthCheck
from eaip.eventsourcing.integration import EventSourcingRuntimeModule
from eaip.eventsourcing.models import (
    EventSourcingConfig,
    EventStream,
    Projection,
    ProjectionConfig,
    ProjectionStatus,
    StoredEvent,
)
from eaip.eventsourcing.projections import ProjectionBuilder
from eaip.eventsourcing.replay import EventReplayService
from eaip.eventsourcing.snapshots import SnapshotEntry, SnapshotService
from eaip.eventsourcing.store import EventStore

__all__ = [
    "ConcurrencyError",
    "EventReplayService",
    "EventSourcingConfig",
    "EventSourcingError",
    "EventSourcingHealthCheck",
    "EventSourcingRuntimeModule",
    "EventStore",
    "EventStoreError",
    "EventStored",
    "EventStream",
    "Projection",
    "ProjectionBuilder",
    "ProjectionBuilt",
    "ProjectionConfig",
    "ProjectionNotFoundError",
    "ProjectionRebuilt",
    "ProjectionRegistered",
    "ProjectionStatus",
    "ReplayCompleted",
    "ReplayError",
    "ReplayStarted",
    "SnapshotCreated",
    "SnapshotEntry",
    "SnapshotNotFoundError",
    "SnapshotService",
    "StoredEvent",
]
