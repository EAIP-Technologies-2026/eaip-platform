"""Tests for config backup domain events."""

from __future__ import annotations

import pydantic
import pytest

from eaip.configbackup.events import SnapshotArchived, SnapshotCreated, SnapshotRestored


class TestSnapshotCreated:
    def test_create(self) -> None:
        event = SnapshotCreated(snapshot_id="s1", resource_id="r1", version=1)
        assert event.snapshot_id == "s1"
        assert event.resource_id == "r1"
        assert event.version == 1
        assert event.event_type == "eaip.configbackup.snapshot_created"


class TestSnapshotRestored:
    def test_create(self) -> None:
        event = SnapshotRestored(restore_id="rp1", snapshot_id="s1", restored_by="alice")
        assert event.restore_id == "rp1"
        assert event.snapshot_id == "s1"
        assert event.restored_by == "alice"
        assert event.event_type == "eaip.configbackup.snapshot_restored"


class TestSnapshotArchived:
    def test_create(self) -> None:
        event = SnapshotArchived(snapshot_id="s1", resource_id="r1")
        assert event.snapshot_id == "s1"
        assert event.resource_id == "r1"
        assert event.event_type == "eaip.configbackup.snapshot_archived"

    def test_frozen(self) -> None:
        event = SnapshotArchived(snapshot_id="s1", resource_id="r1")
        with pytest.raises(pydantic.ValidationError):
            event.snapshot_id = "s2"  # type: ignore[misc]
