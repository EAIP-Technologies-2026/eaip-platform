"""Domain events for the sandbox environment manager."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from eaip.events.event import DomainEvent


class EnvironmentCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.sandbox.environment.created"

    environment_id: str
    name: str
    environment_type: str


class EnvironmentDeleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.sandbox.environment.deleted"

    environment_id: str


class SandboxCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.sandbox.sandbox.created"

    sandbox_id: str
    name: str
    environment_id: str
    template_id: str
    ttl_minutes: int
    expires_at: datetime


class SandboxStopped(DomainEvent):
    event_type: ClassVar[str] = "eaip.sandbox.sandbox.stopped"

    sandbox_id: str
    environment_id: str
    reason: str


class SandboxExpired(DomainEvent):
    event_type: ClassVar[str] = "eaip.sandbox.sandbox.expired"

    sandbox_id: str
    environment_id: str
    expires_at: datetime


__all__ = [
    "EnvironmentCreated",
    "EnvironmentDeleted",
    "SandboxCreated",
    "SandboxExpired",
    "SandboxStopped",
]
