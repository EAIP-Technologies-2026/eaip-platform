"""Tests for Archive domain events."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.archive.events import (
    ArchiveCreated,
    ArchiveEvent,
    ArchiveFailed,
    ArchivePruned,
    ArchiveRestored,
    RetentionPolicyApplied,
)
from eaip.events.event import DomainEvent


class TestArchiveCreated:
    def test_fields(self) -> None:
        event = ArchiveCreated(
            record_id="rec_1",
            source_collection="orders",
            size_bytes=1024,
        )
        assert event.record_id == "rec_1"
        assert event.source_collection == "orders"
        assert event.size_bytes == 1024
        assert isinstance(event.occurred_at, datetime)
        assert isinstance(event, DomainEvent)

    def test_event_type(self) -> None:
        assert ArchiveCreated.event_type == "eaip.archive.created"

    def test_frozen(self) -> None:
        e = ArchiveCreated(record_id="r1", source_collection="c1")
        with pytest.raises(ValueError):
            e.record_id = "r2"  # type: ignore[misc]


class TestArchiveRestored:
    def test_fields(self) -> None:
        event = ArchiveRestored(
            record_id="rec_1",
            target_collection="orders_restored",
        )
        assert event.record_id == "rec_1"
        assert event.target_collection == "orders_restored"
        assert isinstance(event, DomainEvent)

    def test_event_type(self) -> None:
        assert ArchiveRestored.event_type == "eaip.archive.restored"


class TestArchivePruned:
    def test_fields(self) -> None:
        event = ArchivePruned(
            policy_id="p_1",
            items_removed=10,
            bytes_freed=2048,
        )
        assert event.policy_id == "p_1"
        assert event.items_removed == 10
        assert event.bytes_freed == 2048
        assert isinstance(event, DomainEvent)

    def test_event_type(self) -> None:
        assert ArchivePruned.event_type == "eaip.archive.pruned"


class TestRetentionPolicyApplied:
    def test_fields(self) -> None:
        event = RetentionPolicyApplied(
            policy_id="p_1",
            affected_items=5,
        )
        assert event.policy_id == "p_1"
        assert event.affected_items == 5
        assert isinstance(event, DomainEvent)

    def test_event_type(self) -> None:
        assert RetentionPolicyApplied.event_type == "eaip.archive.retention_policy_applied"


class TestArchiveFailed:
    def test_fields(self) -> None:
        event = ArchiveFailed(
            record_id="rec_1",
            error_message="storage unavailable",
            source_collection="orders",
        )
        assert event.record_id == "rec_1"
        assert event.error_message == "storage unavailable"
        assert event.source_collection == "orders"
        assert isinstance(event, DomainEvent)

    def test_event_type(self) -> None:
        assert ArchiveFailed.event_type == "eaip.archive.failed"


class TestArchiveEventUnion:
    def test_union_includes_all_events(self) -> None:
        created: ArchiveEvent = ArchiveCreated(record_id="r1", source_collection="c1")
        restored: ArchiveEvent = ArchiveRestored(record_id="r1", target_collection="c1")
        pruned: ArchiveEvent = ArchivePruned(policy_id="p1", items_removed=1, bytes_freed=1)
        applied: ArchiveEvent = RetentionPolicyApplied(policy_id="p1", affected_items=1)
        failed: ArchiveEvent = ArchiveFailed(
            record_id="r1", error_message="err", source_collection="c1"
        )
        assert isinstance(created, ArchiveCreated)
        assert isinstance(restored, ArchiveRestored)
        assert isinstance(pruned, ArchivePruned)
        assert isinstance(applied, RetentionPolicyApplied)
        assert isinstance(failed, ArchiveFailed)
