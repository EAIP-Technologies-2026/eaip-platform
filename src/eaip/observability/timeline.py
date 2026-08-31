from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ObservabilityEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    event_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    tenant_id: str
    correlation_id: str = ""
    actor: str = ""
    resource: str = ""
    action: str = ""
    status: str = "ok"
    duration_ms: float = 0.0
    error: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class TimelineStore:
    def __init__(self) -> None:
        self._events: dict[str, list[ObservabilityEvent]] = defaultdict(list)
        self._by_correlation: dict[str, list[ObservabilityEvent]] = defaultdict(list)

    def record(self, event: ObservabilityEvent) -> ObservabilityEvent:
        self._events[event.tenant_id].append(event)
        if event.correlation_id:
            self._by_correlation[event.correlation_id].append(event)
        if len(self._events[event.tenant_id]) > 5000:
            self._events[event.tenant_id] = self._events[event.tenant_id][-5000:]
        return event

    def timeline_for(self, tenant_id: str, correlation_id: str) -> list[ObservabilityEvent]:
        all_events = self._by_correlation.get(correlation_id, [])
        return [e for e in all_events if e.tenant_id == tenant_id]

    def list_for_tenant(self, tenant_id: str, limit: int = 100) -> list[ObservabilityEvent]:
        return list(reversed(self._events.get(tenant_id, [])))[:limit]

    def reconstruct(self, tenant_id: str, correlation_id: str) -> dict[str, Any]:
        events = self.timeline_for(tenant_id, correlation_id)
        return {
            "correlation_id": correlation_id,
            "tenant_id": tenant_id,
            "events": [e.model_dump(mode="json") for e in sorted(events, key=lambda x: x.timestamp)],
            "count": len(events),
        }


_timeline = TimelineStore()


def get_timeline_store() -> TimelineStore:
    return _timeline


def new_correlation_id() -> str:
    return uuid.uuid4().hex[:16]


__all__ = ["ObservabilityEvent", "TimelineStore", "get_timeline_store", "new_correlation_id"]
