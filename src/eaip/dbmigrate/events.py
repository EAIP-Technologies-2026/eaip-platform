"""Domain events for database migration."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class ScriptCreated(DomainEvent):
    """Emitted when a new migration script is created."""

    event_type: ClassVar[str] = "eaip.dbmigrate.script.created"

    script_id: str
    name: str
    version: str
    database_type: str
    author: str


class MigrationExecuted(DomainEvent):
    """Emitted when a migration script is executed."""

    event_type: ClassVar[str] = "eaip.dbmigrate.migration.executed"

    execution_id: str
    script_id: str
    environment: str
    success: bool
    output: str = Field(default="")


class MigrationRolledBack(DomainEvent):
    """Emitted when a migration is rolled back."""

    event_type: ClassVar[str] = "eaip.dbmigrate.migration.rolled_back"

    script_id: str
    environment: str
    reason: str = Field(default="")
    details: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "MigrationExecuted",
    "MigrationRolledBack",
    "ScriptCreated",
]
