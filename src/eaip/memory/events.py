"""Memory Engine domain events."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent
from eaip.memory.models import MemoryScope, MemoryType


class MemoryEngineEvent(DomainEvent):
    """Base event for all Memory Engine events."""

    event_type: ClassVar[str] = "eaip.memory.event"


class MemoryCreated(MemoryEngineEvent):
    """Published when a memory item is created."""

    event_type: ClassVar[str] = "eaip.memory.memory.created"
    memory_id: str
    memory_type: MemoryType
    scope: MemoryScope
    importance: float
    tags: tuple[str, ...] = ()


class MemoryUpdated(MemoryEngineEvent):
    """Published when a memory item is updated."""

    event_type: ClassVar[str] = "eaip.memory.memory.updated"
    memory_id: str
    scope: MemoryScope
    version: int
    changes: tuple[str, ...] = ()


class MemoryDeleted(MemoryEngineEvent):
    """Published when a memory item is deleted."""

    event_type: ClassVar[str] = "eaip.memory.memory.deleted"
    memory_id: str
    scope: MemoryScope
    reason: str = ""


class MemoryRetrieved(MemoryEngineEvent):
    """Published when a memory item is retrieved by ID."""

    event_type: ClassVar[str] = "eaip.memory.memory.retrieved"
    memory_id: str
    scope: MemoryScope


class MemoryAccessTracked(MemoryEngineEvent):
    """Published when a memory item is accessed (read or write)."""

    event_type: ClassVar[str] = "eaip.memory.memory.access_tracked"
    memory_id: str
    scope: MemoryScope
    access_count: int


class MemoryExpired(MemoryEngineEvent):
    """Published when a memory item expires."""

    event_type: ClassVar[str] = "eaip.memory.memory.expired"
    memory_id: str
    scope: MemoryScope
    memory_type: MemoryType
    reason: str = ""


class MemoryArchived(MemoryEngineEvent):
    """Published when a memory item is archived."""

    event_type: ClassVar[str] = "eaip.memory.memory.archived"
    memory_id: str
    scope: MemoryScope


class MemoryConsolidated(MemoryEngineEvent):
    """Published when memories are consolidated."""

    event_type: ClassVar[str] = "eaip.memory.memory.consolidated"
    source_ids: tuple[str, ...] = ()
    target_id: str = ""
    consolidated_count: int = 0


class MemorySummarized(MemoryEngineEvent):
    """Published when a memory is summarized."""

    event_type: ClassVar[str] = "eaip.memory.memory.summarized"
    memory_id: str
    scope: MemoryScope


class MemoryRetrievalExecuted(MemoryEngineEvent):
    """Published after a retrieval query is executed."""

    event_type: ClassVar[str] = "eaip.memory.retrieval.executed"
    query: str
    memory_type: MemoryType | None = None
    result_count: int
    duration_ms: float


class MemorySearchExecuted(MemoryEngineEvent):
    """Published after a search operation completes."""

    event_type: ClassVar[str] = "eaip.memory.search.executed"
    query: str
    filters: dict[str, Any] = {}
    result_count: int
    duration_ms: float


__all__ = [
    "MemoryAccessTracked",
    "MemoryArchived",
    "MemoryConsolidated",
    "MemoryCreated",
    "MemoryDeleted",
    "MemoryEngineEvent",
    "MemoryExpired",
    "MemoryRetrievalExecuted",
    "MemoryRetrieved",
    "MemorySearchExecuted",
    "MemorySummarized",
    "MemoryUpdated",
]
