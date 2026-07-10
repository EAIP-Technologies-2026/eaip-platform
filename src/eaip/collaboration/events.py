"""Collaboration domain events."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.collaboration.models import SessionStatus, TaskStatus
from eaip.events.event import DomainEvent


class CollaborationSessionCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.collaboration.session.created"
    session_id: str = ""
    name: str = ""
    session_type: str = ""
    agent_count: int = 0


class CollaborationSessionStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.collaboration.session.started"
    session_id: str = ""
    name: str = ""
    strategy: str = ""


class CollaborationSessionCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.collaboration.session.completed"
    session_id: str = ""
    status: SessionStatus = SessionStatus.COMPLETED
    duration_ms: float = 0.0
    task_count: int = 0
    consensus_reached: bool = False


class CollaborationSessionFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.collaboration.session.failed"
    session_id: str = ""
    error: str = ""
    duration_ms: float = 0.0


class TaskAssigned(DomainEvent):
    event_type: ClassVar[str] = "eaip.collaboration.task.assigned"
    task_id: str = ""
    session_id: str = ""
    agent_id: str = ""
    task_type: str = ""
    description: str = ""


class TaskCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.collaboration.task.completed"
    task_id: str = ""
    session_id: str = ""
    agent_id: str = ""
    duration_ms: float = 0.0
    output: str = ""


class TaskFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.collaboration.task.failed"
    task_id: str = ""
    session_id: str = ""
    agent_id: str = ""
    error: str = ""


class DelegationRequested(DomainEvent):
    event_type: ClassVar[str] = "eaip.collaboration.delegation.requested"
    delegation_id: str = ""
    from_agent_id: str = ""
    to_agent_id: str = ""
    task_description: str = ""


class DelegationAccepted(DomainEvent):
    event_type: ClassVar[str] = "eaip.collaboration.delegation.accepted"
    delegation_id: str = ""
    to_agent_id: str = ""


class DelegationRejected(DomainEvent):
    event_type: ClassVar[str] = "eaip.collaboration.delegation.rejected"
    delegation_id: str = ""
    to_agent_id: str = ""
    reason: str = ""


class ApprovalRequested(DomainEvent):
    event_type: ClassVar[str] = "eaip.collaboration.approval.requested"
    approval_id: str = ""
    session_id: str = ""
    step_id: str = ""
    approver_count: int = 0


class ApprovalCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.collaboration.approval.completed"
    approval_id: str = ""
    approver_id: str = ""


class ApprovalRejected(DomainEvent):
    event_type: ClassVar[str] = "eaip.collaboration.approval.rejected"
    approval_id: str = ""
    approver_id: str = ""
    reason: str = ""


class StateUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.collaboration.state.updated"
    session_id: str = ""
    key: str = ""
    agent_id: str = ""
    version: int = 0


class ConsensusReached(DomainEvent):
    event_type: ClassVar[str] = "eaip.collaboration.consensus.reached"
    session_id: str = ""
    threshold: float = 0.0
    agreement_count: int = 0
    total_agents: int = 0


CollaborationEvent = (
    CollaborationSessionCreated
    | CollaborationSessionStarted
    | CollaborationSessionCompleted
    | CollaborationSessionFailed
    | TaskAssigned
    | TaskCompleted
    | TaskFailed
    | DelegationRequested
    | DelegationAccepted
    | DelegationRejected
    | ApprovalRequested
    | ApprovalCompleted
    | ApprovalRejected
    | StateUpdated
    | ConsensusReached
)


__all__ = [
    "ApprovalCompleted",
    "ApprovalRejected",
    "ApprovalRequested",
    "CollaborationEvent",
    "CollaborationSessionCompleted",
    "CollaborationSessionCreated",
    "CollaborationSessionFailed",
    "CollaborationSessionStarted",
    "ConsensusReached",
    "DelegationAccepted",
    "DelegationRejected",
    "DelegationRequested",
    "StateUpdated",
    "TaskAssigned",
    "TaskCompleted",
    "TaskFailed",
]
