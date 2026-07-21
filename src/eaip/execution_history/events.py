"""Domain events published by the execution history subsystem."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent
from eaip.execution_history.models import ExecutionRecord


class ExecutionRecordCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.execution_history.record.created"
    record: ExecutionRecord


class ExecutionRecordUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.execution_history.record.updated"
    record_id: str
    changes: dict[str, Any]


class ExecutionHistoryQueried(DomainEvent):
    event_type: ClassVar[str] = "eaip.execution_history.queried"
    query: dict[str, Any]
    result_count: int


class ExecutionHistoryArchived(DomainEvent):
    event_type: ClassVar[str] = "eaip.execution_history.archived"
    records_archived: int
    older_than_days: int


class ExecutionHistoryPurged(DomainEvent):
    event_type: ClassVar[str] = "eaip.execution_history.purged"
    records_purged: int
    older_than_days: int


class ExecutionHistoryExported(DomainEvent):
    event_type: ClassVar[str] = "eaip.execution_history.exported"
    record_count: int
    format: str
    destination: str


class ExecutionHistoryCompacted(DomainEvent):
    event_type: ClassVar[str] = "eaip.execution_history.compacted"
    records_compacted: int
    duration_ms: float


class ExecutionHistoryAnalyticsComputed(DomainEvent):
    event_type: ClassVar[str] = "eaip.execution_history.analytics_computed"
    stats: dict[str, Any]


__all__ = [
    "ExecutionHistoryAnalyticsComputed",
    "ExecutionHistoryArchived",
    "ExecutionHistoryCompacted",
    "ExecutionHistoryExported",
    "ExecutionHistoryPurged",
    "ExecutionHistoryQueried",
    "ExecutionRecordCreated",
    "ExecutionRecordUpdated",
]
