"""Domain events published by the schema registry subsystem."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class SchemaRegistered(DomainEvent):
    event_type: ClassVar[str] = "schema.registered"
    schema_id: str
    name: str
    schema_type: str
    version: str


class SchemaVersionCreated(DomainEvent):
    event_type: ClassVar[str] = "schema.version.created"
    schema_id: str
    version: str
    change_log: str


class SchemaDeprecated(DomainEvent):
    event_type: ClassVar[str] = "schema.deprecated"
    schema_id: str
    reason: str


class SchemaSuperseded(DomainEvent):
    event_type: ClassVar[str] = "schema.superseded"
    schema_id: str
    superseded_by: str
    reason: str


class SchemaValidated(DomainEvent):
    event_type: ClassVar[str] = "schema.validated"
    schema_id: str
    version: str
    valid: bool
    error_count: int
    warning_count: int


class SchemaCompatibilityChecked(DomainEvent):
    event_type: ClassVar[str] = "schema.compatibility.checked"
    schema_id: str
    source_version: str
    target_version: str
    compatible: bool
    check_type: str


__all__ = [
    "SchemaCompatibilityChecked",
    "SchemaDeprecated",
    "SchemaRegistered",
    "SchemaSuperseded",
    "SchemaValidated",
    "SchemaVersionCreated",
]
