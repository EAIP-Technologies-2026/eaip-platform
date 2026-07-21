"""Runtime domain events — published via EventBus during runtime lifecycle."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class RuntimeEvent(DomainEvent):
    """Base event for all Runtime events."""

    event_type: ClassVar[str] = "eaip.runtime.event"


class RuntimeStarted(RuntimeEvent):
    """Published when the runtime starts."""

    event_type: ClassVar[str] = "eaip.runtime.started"
    run_id: str | None = None


class RuntimeStopped(RuntimeEvent):
    """Published when the runtime stops."""

    event_type: ClassVar[str] = "eaip.runtime.stopped"
    uptime_seconds: float = 0.0


class RuntimePaused(RuntimeEvent):
    """Published when the runtime is paused."""

    event_type: ClassVar[str] = "eaip.runtime.paused"


class RuntimeRecovered(RuntimeEvent):
    """Published when the runtime recovers from a failure."""

    event_type: ClassVar[str] = "eaip.runtime.recovered"


class RuntimeHealthChanged(RuntimeEvent):
    """Published when overall runtime health changes."""

    event_type: ClassVar[str] = "eaip.runtime.health_changed"
    previous_status: str = ""
    new_status: str = ""


class MissionCreated(RuntimeEvent):
    """Published when a mission is created."""

    event_type: ClassVar[str] = "eaip.mission.created"
    mission_id: str
    name: str


class MissionStarted(RuntimeEvent):
    """Published when a mission begins execution."""

    event_type: ClassVar[str] = "eaip.mission.started"
    mission_id: str


class MissionCompleted(RuntimeEvent):
    """Published when a mission completes successfully."""

    event_type: ClassVar[str] = "eaip.mission.completed"
    mission_id: str
    duration_ms: float = 0.0
    result: str = ""


class MissionFailed(RuntimeEvent):
    """Published when a mission fails."""

    event_type: ClassVar[str] = "eaip.mission.failed"
    mission_id: str
    error: str = ""


class MissionCancelled(RuntimeEvent):
    """Published when a mission is cancelled."""

    event_type: ClassVar[str] = "eaip.mission.cancelled"
    mission_id: str


__all__ = [
    "MissionCancelled",
    "MissionCompleted",
    "MissionCreated",
    "MissionFailed",
    "MissionStarted",
    "RuntimeEvent",
    "RuntimeHealthChanged",
    "RuntimePaused",
    "RuntimeRecovered",
    "RuntimeStarted",
    "RuntimeStopped",
]
