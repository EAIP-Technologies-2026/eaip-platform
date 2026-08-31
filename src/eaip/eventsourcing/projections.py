"""Projection builder — register, build, rebuild, and manage projections."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from eaip.eventsourcing.exceptions import ProjectionNotFoundError
from eaip.eventsourcing.models import Projection, ProjectionConfig, ProjectionStatus, StoredEvent
from eaip.logging.context import get_logger

ProjectionHandler = Callable[[StoredEvent, dict[str, Any]], Awaitable[dict[str, Any]]]


class ProjectionBuilder:
    def __init__(self, config: ProjectionConfig | None = None) -> None:
        self._config = config or ProjectionConfig()
        self._projections: dict[str, Projection] = {}
        self._handlers: dict[str, ProjectionHandler] = {}
        self._log = get_logger("eaip.eventsourcing.projections")

    @property
    def config(self) -> ProjectionConfig:
        return self._config

    def register_projection(
        self,
        projection_id: str,
        name: str,
        handler: ProjectionHandler,
        *,
        aggregate_types: tuple[str, ...] | None = None,
        handler_type: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> Projection:
        projection = Projection(
            id=projection_id,
            name=name,
            aggregate_types=aggregate_types or (),
            handler_type=handler_type,
            metadata=metadata or {},
        )
        self._projections[projection_id] = projection
        self._handlers[projection_id] = handler
        self._log.info("projection.registered", projection_id=projection_id, name=name)
        return projection

    def unregister_projection(self, projection_id: str) -> None:
        if projection_id not in self._projections:
            raise ProjectionNotFoundError(f"Projection {projection_id} not found")
        del self._projections[projection_id]
        self._handlers.pop(projection_id, None)
        self._log.info("projection.unregistered", projection_id=projection_id)

    def get_projection(self, projection_id: str) -> Projection:
        proj = self._projections.get(projection_id)
        if proj is None:
            raise ProjectionNotFoundError(f"Projection {projection_id} not found")
        return proj

    def list_projections(self) -> list[Projection]:
        return list(self._projections.values())

    async def build_projection(self, projection_id: str, events: list[StoredEvent]) -> Projection:
        proj = self.get_projection(projection_id)
        handler = self._handlers.get(projection_id)
        if handler is None:
            raise ProjectionNotFoundError(f"No handler registered for projection {projection_id}")

        state = dict(proj.state)
        processed = 0

        for event in events:
            try:
                state = await handler(event, state)
                processed += 1
            except Exception:
                self._log.exception(
                    "projection.event.failed", projection_id=projection_id, event_id=event.id
                )
                proj = proj.model_copy(update={"status": ProjectionStatus.FAILED})
                self._projections[projection_id] = proj
                raise

        last_event = events[-1] if events else None
        update: dict[str, Any] = {
            "state": state,
            "last_processed_event_id": last_event.id
            if last_event
            else proj.last_processed_event_id,
            "status": ProjectionStatus.ACTIVE,
        }
        if last_event:
            from eaip.shared.time import utc_now

            update["last_processed_at"] = utc_now()

        proj = proj.model_copy(update=update)
        self._projections[projection_id] = proj
        return proj

    async def rebuild_all(
        self, events_by_projection: dict[str, list[StoredEvent]]
    ) -> list[Projection]:
        results = []
        for pid, events in events_by_projection.items():
            proj = await self.build_projection(pid, events)
            results.append(proj)
        return results

    async def process_event(self, event: StoredEvent) -> list[Projection]:
        updated = []
        for pid, proj in list(self._projections.items()):
            if proj.status != ProjectionStatus.ACTIVE:
                continue
            if proj.aggregate_types and event.aggregate_type not in proj.aggregate_types:
                continue

            handler = self._handlers.get(pid)
            if handler is None:
                continue

            try:
                new_state = await handler(event, dict(proj.state))
                from eaip.shared.time import utc_now

                proj = proj.model_copy(
                    update={
                        "state": new_state,
                        "last_processed_event_id": event.id,
                        "last_processed_at": utc_now(),
                    }
                )
                self._projections[pid] = proj
                updated.append(proj)
            except Exception:
                self._log.exception(
                    "projection.process.failed", projection_id=pid, event_id=event.id
                )
                proj = proj.model_copy(update={"status": ProjectionStatus.FAILED})
                self._projections[pid] = proj

        return updated


__all__ = ["ProjectionBuilder"]
