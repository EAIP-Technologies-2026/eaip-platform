"""Runtime module integration for the event sourcing subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.eventsourcing.health import EventSourcingHealthCheck
from eaip.eventsourcing.models import EventSourcingConfig, ProjectionConfig
from eaip.eventsourcing.projections import ProjectionBuilder
from eaip.eventsourcing.replay import EventReplayService
from eaip.eventsourcing.snapshots import SnapshotService
from eaip.eventsourcing.store import EventStore
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class EventSourcingRuntimeModule:
    name: str = "eventsourcing"

    def __init__(
        self,
        config: EventSourcingConfig | None = None,
        projection_config: ProjectionConfig | None = None,
        store: EventStore | None = None,
        projection_builder: ProjectionBuilder | None = None,
        replay_service: EventReplayService | None = None,
        snapshot_service: SnapshotService | None = None,
    ) -> None:
        self._config = config or EventSourcingConfig()
        self._projection_config = projection_config or ProjectionConfig()
        self._store = store or EventStore()
        self._projection_builder = projection_builder or ProjectionBuilder(
            config=self._projection_config
        )
        self._replay_service = replay_service or EventReplayService(store=self._store)
        self._snapshot_service = snapshot_service or SnapshotService(
            store=self._store,
            snapshot_frequency=self._config.snapshot_frequency,
        )
        self._log = get_logger("eaip.eventsourcing.integration")

    @property
    def store(self) -> EventStore:
        return self._store

    @property
    def projection_builder(self) -> ProjectionBuilder:
        return self._projection_builder

    @property
    def replay_service(self) -> EventReplayService:
        return self._replay_service

    @property
    def snapshot_service(self) -> SnapshotService:
        return self._snapshot_service

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("eventsourcing.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.eventsourcing",
            title="Event Sourcing",
            description="Event store, event replay, projection building, snapshot management, and CQRS support",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("eventsourcing", "event-store", "cqrs", "projections", "snapshots", "replay"),
        )
        platform.capabilities.register(capability)
        platform.health.register(EventSourcingHealthCheck(store=self._store))
        self._log.info("eventsourcing.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("eventsourcing.module.stopping")


__all__ = ["EventSourcingRuntimeModule"]
