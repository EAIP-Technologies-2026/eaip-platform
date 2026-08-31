"""Health check for the event sourcing subsystem."""

from __future__ import annotations

from eaip.eventsourcing.store import EventStore
from eaip.health.checks import HealthReport, HealthStatus


class EventSourcingHealthCheck:
    name: str = "eventsourcing"

    def __init__(self, store: EventStore) -> None:
        self._store = store

    async def check(self) -> HealthReport:
        error_details: list[str] = []
        total_events = self._store.count_events()

        if total_events == 0:
            error_details.append("No events stored")

        status = HealthStatus.HEALTHY
        if error_details:
            status = HealthStatus.DEGRADED

        return HealthReport(
            component="eventsourcing",
            status=status,
            message="; ".join(error_details)
            if error_details
            else "Event sourcing subsystem is operational",
            details={
                "total_events": total_events,
            },
        )


__all__ = ["EventSourcingHealthCheck"]
