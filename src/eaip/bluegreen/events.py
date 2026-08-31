"""Domain events for blue-green deployment management."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class SwitchStarted(DomainEvent):
    """Emitted when a traffic switch operation begins."""

    event_type: ClassVar[str] = "eaip.bluegreen.switch.started"

    switch_id: str
    from_env: str
    to_env: str
    strategy: str


class SwitchCompleted(DomainEvent):
    """Emitted when a traffic switch completes successfully."""

    event_type: ClassVar[str] = "eaip.bluegreen.switch.completed"

    switch_id: str
    from_env: str
    to_env: str
    new_active: str


class SwitchRolledBack(DomainEvent):
    """Emitted when a traffic switch is rolled back."""

    event_type: ClassVar[str] = "eaip.bluegreen.switch.rolled_back"

    switch_id: str
    from_env: str
    to_env: str
    reason: str


class HealthCheckFailed(DomainEvent):
    """Emitted when health checks fail during a switch."""

    event_type: ClassVar[str] = "eaip.bluegreen.health_check.failed"

    switch_id: str
    environment: str
    message: str


__all__ = [
    "HealthCheckFailed",
    "SwitchCompleted",
    "SwitchRolledBack",
    "SwitchStarted",
]
