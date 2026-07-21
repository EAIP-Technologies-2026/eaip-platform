"""Domain events for the credential rotator."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class CredentialRotated(DomainEvent):
    event_type: ClassVar[str] = "eaip.credrot.rotated"

    credential_id: str
    name: str
    type: str
    rotated_at: datetime


class RotationScheduled(DomainEvent):
    event_type: ClassVar[str] = "eaip.credrot.scheduled"

    schedule_id: str
    credential_id: str
    scheduled_at: datetime


class RotationFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.credrot.failed"

    credential_id: str
    name: str
    error: str
    details: dict[str, Any] = Field(default_factory=dict)
