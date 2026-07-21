"""Tests for datasync domain events."""

from __future__ import annotations

import pytest

from eaip.datasync.events import SyncCompleted, SyncFailed, SyncJobCreated, SyncStarted
from eaip.datasync.models import SyncType
from eaip.events.event import DomainEvent


class TestSyncJobCreated:
    def test_defaults(self) -> None:
        e = SyncJobCreated(job_id="j1", name="sync-db", sync_type=SyncType.FULL)
        assert e.event_type == "eaip.datasync.job.created"
        assert isinstance(e, DomainEvent)

    def test_with_values(self) -> None:
        e = SyncJobCreated(job_id="j1", name="sync-db", sync_type=SyncType.FULL)
        assert e.job_id == "j1"
        assert e.name == "sync-db"
        assert e.sync_type == SyncType.FULL

    def test_frozen(self) -> None:
        e = SyncJobCreated(job_id="j1", name="sync-db", sync_type=SyncType.FULL)
        with pytest.raises((ValueError, TypeError)):
            e.job_id = "j2"


class TestSyncStarted:
    def test_defaults(self) -> None:
        e = SyncStarted(run_id="r1", job_id="j1", started_at="2025-01-01T00:00:00Z")  # type: ignore[arg-type]
        assert e.event_type == "eaip.datasync.sync.started"


class TestSyncCompleted:
    def test_defaults(self) -> None:
        e = SyncCompleted(run_id="r1", job_id="j1")
        assert e.event_type == "eaip.datasync.sync.completed"
        assert e.items_synced == 0

    def test_with_values(self) -> None:
        e = SyncCompleted(
            run_id="r1", job_id="j1", items_synced=100, items_failed=2, duration_seconds=45.5
        )
        assert e.items_synced == 100
        assert e.items_failed == 2
        assert e.duration_seconds == 45.5


class TestSyncFailed:
    def test_defaults(self) -> None:
        e = SyncFailed(run_id="r1", job_id="j1")
        assert e.event_type == "eaip.datasync.sync.failed"
        assert e.error_message == ""

    def test_with_values(self) -> None:
        e = SyncFailed(run_id="r1", job_id="j1", error_message="timeout")
        assert e.error_message == "timeout"


class TestEventTypes:
    def test_all_have_unique_event_types(self) -> None:
        events = [SyncJobCreated, SyncStarted, SyncCompleted, SyncFailed]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))
