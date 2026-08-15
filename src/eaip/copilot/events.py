"""Domain events raised by the copilot package."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class ApprovalRequested(DomainEvent):
    """Published when a governed action waits for human approval."""

    event_type: ClassVar[str] = "eaip.copilot.approval_requested"

    approval_id: str
    tool_name: str
    requester_id: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ApprovalResolved(DomainEvent):
    """Published when an approval request is approved or rejected."""

    event_type: ClassVar[str] = "eaip.copilot.approval_resolved"

    approval_id: str
    approved: bool
    decided_by: str


class ConductorTurnCompleted(DomainEvent):
    """Published after a full Conductor turn has been processed."""

    event_type: ClassVar[str] = "eaip.copilot.turn_completed"

    turn_id: str
    actor_id: str
    reply: str
    tool_events: tuple[str, ...] = Field(default_factory=tuple)


__all__ = ["ApprovalRequested", "ApprovalResolved", "ConductorTurnCompleted"]
