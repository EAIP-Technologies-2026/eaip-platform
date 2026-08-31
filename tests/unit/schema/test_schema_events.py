"""Tests for schema domain events."""

from __future__ import annotations

from eaip.events.event import DomainEvent
from eaip.schema.events import (
    SchemaCompatibilityChecked,
    SchemaDeprecated,
    SchemaRegistered,
    SchemaSuperseded,
    SchemaValidated,
    SchemaVersionCreated,
)


class TestSchemaRegistered:
    def test_event_type(self) -> None:
        event = SchemaRegistered(
            schema_id="s1", name="TestSchema", schema_type="json_schema", version="1"
        )
        assert event.event_type == "schema.registered"
        assert isinstance(event, DomainEvent)

    def test_content(self) -> None:
        event = SchemaRegistered(
            schema_id="s1", name="OrderSchema", schema_type="avro", version="1.0.0"
        )
        assert event.schema_id == "s1"
        assert event.name == "OrderSchema"
        assert event.schema_type == "avro"
        assert event.version == "1.0.0"


class TestSchemaVersionCreated:
    def test_event_type(self) -> None:
        event = SchemaVersionCreated(schema_id="s1", version="2", change_log="Added field")
        assert event.event_type == "schema.version.created"

    def test_content(self) -> None:
        event = SchemaVersionCreated(schema_id="s1", version="2.0.0", change_log="Breaking change")
        assert event.schema_id == "s1"
        assert event.version == "2.0.0"
        assert event.change_log == "Breaking change"


class TestSchemaDeprecated:
    def test_event_type(self) -> None:
        event = SchemaDeprecated(schema_id="s1", reason="Replaced by v2")
        assert event.event_type == "schema.deprecated"

    def test_content(self) -> None:
        event = SchemaDeprecated(schema_id="s1", reason="No longer in use")
        assert event.schema_id == "s1"
        assert event.reason == "No longer in use"


class TestSchemaSuperseded:
    def test_event_type(self) -> None:
        event = SchemaSuperseded(schema_id="s1", superseded_by="s2", reason="Upgraded")
        assert event.event_type == "schema.superseded"

    def test_content(self) -> None:
        event = SchemaSuperseded(schema_id="s1", superseded_by="s2", reason="New version available")
        assert event.schema_id == "s1"
        assert event.superseded_by == "s2"
        assert event.reason == "New version available"


class TestSchemaValidated:
    def test_event_type(self) -> None:
        event = SchemaValidated(
            schema_id="s1", version="1", valid=True, error_count=0, warning_count=0
        )
        assert event.event_type == "schema.validated"

    def test_content(self) -> None:
        event = SchemaValidated(
            schema_id="s1", version="1.0.0", valid=False, error_count=2, warning_count=1
        )
        assert event.schema_id == "s1"
        assert event.version == "1.0.0"
        assert event.valid is False
        assert event.error_count == 2
        assert event.warning_count == 1


class TestSchemaCompatibilityChecked:
    def test_event_type(self) -> None:
        event = SchemaCompatibilityChecked(
            schema_id="s1",
            source_version="1",
            target_version="2",
            compatible=True,
            check_type="backward",
        )
        assert event.event_type == "schema.compatibility.checked"

    def test_content(self) -> None:
        event = SchemaCompatibilityChecked(
            schema_id="s1",
            source_version="1.0.0",
            target_version="2.0.0",
            compatible=False,
            check_type="full",
        )
        assert event.schema_id == "s1"
        assert event.source_version == "1.0.0"
        assert event.target_version == "2.0.0"
        assert event.compatible is False
        assert event.check_type == "full"


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(SchemaRegistered, DomainEvent)
        assert issubclass(SchemaVersionCreated, DomainEvent)
        assert issubclass(SchemaDeprecated, DomainEvent)
        assert issubclass(SchemaSuperseded, DomainEvent)
        assert issubclass(SchemaValidated, DomainEvent)
        assert issubclass(SchemaCompatibilityChecked, DomainEvent)
