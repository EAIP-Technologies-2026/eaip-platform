"""Enterprise Brain domain events."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class BrainEvent(DomainEvent):
    """Base event for all Enterprise Brain events."""

    event_type: ClassVar[str] = "eaip.brain.event"


class BrainQueryExecuted(BrainEvent):
    """Published when a brain query is executed."""

    event_type: ClassVar[str] = "eaip.brain.query.executed"
    query: str
    source_count: int
    duration_ms: float
    confidence: float = 0.0


class BrainKnowledgeRetrieved(BrainEvent):
    """Published when knowledge sources are queried."""

    event_type: ClassVar[str] = "eaip.brain.knowledge.retrieved"
    query: str
    collections: tuple[str, ...] = ()
    result_count: int
    duration_ms: float


class BrainMemoryRetrieved(BrainEvent):
    """Published when memory sources are queried."""

    event_type: ClassVar[str] = "eaip.brain.memory.retrieved"
    query: str
    result_count: int
    duration_ms: float


class BrainContextBuilt(BrainEvent):
    """Published when context is assembled from sources."""

    event_type: ClassVar[str] = "eaip.brain.context.built"
    query: str
    document_count: int
    total_tokens: int
    duration_ms: float


class DepartmentBrainQueryExecuted(BrainEvent):
    """Published when a department brain query is executed."""

    event_type: ClassVar[str] = "eaip.brain.department.query.executed"
    department_id: str
    query: str
    source_count: int
    duration_ms: float
    confidence: float = 0.0


class BrainAccessDenied(BrainEvent):
    """Published when a brain query is denied by access control."""

    event_type: ClassVar[str] = "eaip.brain.access.denied"
    subject_id: str
    brain_type: str
    department_id: str = ""
    action: str
    reason: str = ""


class BrainSyncCompleted(BrainEvent):
    """Published when department-to-enterprise sync completes."""

    event_type: ClassVar[str] = "eaip.brain.sync.completed"
    department_id: str
    synced_count: int
    duration_ms: float


__all__ = [
    "BrainAccessDenied",
    "BrainContextBuilt",
    "BrainEvent",
    "BrainKnowledgeRetrieved",
    "BrainMemoryRetrieved",
    "BrainQueryExecuted",
    "BrainSyncCompleted",
    "DepartmentBrainQueryExecuted",
]
