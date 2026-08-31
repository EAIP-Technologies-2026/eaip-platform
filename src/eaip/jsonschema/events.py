"""Domain events for the JSON schema service."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class SchemaCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.jsonschema.schema_created"

    schema_id: str
    name: str


class SchemaUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.jsonschema.schema_updated"

    schema_id: str
    name: str
    old_version: int
    new_version: int


class SchemaDeprecated(DomainEvent):
    event_type: ClassVar[str] = "eaip.jsonschema.schema_deprecated"

    schema_id: str
    name: str


class ValidationPerformed(DomainEvent):
    event_type: ClassVar[str] = "eaip.jsonschema.validation_performed"

    schema_id: str
    validation_id: str
    valid: bool
    error_count: int


__all__ = [
    "SchemaCreated",
    "SchemaDeprecated",
    "SchemaUpdated",
    "ValidationPerformed",
]
