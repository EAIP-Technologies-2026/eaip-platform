"""Domain events for the data migration module."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class MigrationStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.datamigrate.migration.started"
    migration_id: str
    migration_name: str
    version: str
    migration_type: str


class MigrationCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.datamigrate.migration.completed"
    migration_id: str
    migration_name: str
    duration_ms: float = Field(default=0.0)


class MigrationFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.datamigrate.migration.failed"
    migration_id: str
    migration_name: str
    error: str
    duration_ms: float = Field(default=0.0)


class MigrationRolledBack(DomainEvent):
    event_type: ClassVar[str] = "eaip.datamigrate.migration.rolled_back"
    migration_id: str
    migration_name: str
    reason: str = Field(default="")
    duration_ms: float = Field(default=0.0)


class MigrationVerified(DomainEvent):
    event_type: ClassVar[str] = "eaip.datamigrate.migration.verified"
    migration_id: str
    migration_name: str
    valid: bool


class BatchStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.datamigrate.batch.started"
    batch_id: str
    batch_name: str
    migration_count: int


class BatchCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.datamigrate.batch.completed"
    batch_id: str
    batch_name: str
    migration_count: int


class BatchFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.datamigrate.batch.failed"
    batch_id: str
    batch_name: str
    error: str


class DataTransformApplied(DomainEvent):
    event_type: ClassVar[str] = "eaip.datamigrate.transform.applied"
    transform_id: str
    transform_name: str
    source_type: str
    target_type: str


class DataTransformValidated(DomainEvent):
    event_type: ClassVar[str] = "eaip.datamigrate.transform.validated"
    transform_id: str
    transform_name: str
    valid: bool
    errors: list[str] = Field(default_factory=list)


__all__ = [
    "BatchCompleted",
    "BatchFailed",
    "BatchStarted",
    "DataTransformApplied",
    "DataTransformValidated",
    "MigrationCompleted",
    "MigrationFailed",
    "MigrationRolledBack",
    "MigrationStarted",
    "MigrationVerified",
]
