"""Domain events for deployment rollback."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent
from eaip.rollbackmgr.models import RollbackStrategy


class RollbackStarted(DomainEvent):
    """Emitted when a rollback begins."""

    event_type: ClassVar[str] = "eaip.rollbackmgr.rollback.started"

    execution_id: str
    deployment_id: str
    strategy: RollbackStrategy
    started_at: datetime


class RollbackCompleted(DomainEvent):
    """Emitted when a rollback completes successfully."""

    event_type: ClassVar[str] = "eaip.rollbackmgr.rollback.completed"

    execution_id: str
    deployment_id: str
    output: str = Field(default="")
    duration_seconds: float = Field(default=0.0)


class RollbackFailed(DomainEvent):
    """Emitted when a rollback fails."""

    event_type: ClassVar[str] = "eaip.rollbackmgr.rollback.failed"

    execution_id: str
    deployment_id: str
    error_message: str = Field(default="")
    details: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "RollbackCompleted",
    "RollbackFailed",
    "RollbackStarted",
]
