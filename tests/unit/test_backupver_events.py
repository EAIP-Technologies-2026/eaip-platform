"""Tests for backup verification domain events."""

from __future__ import annotations

import pytest

from eaip.backupver.events import BackupRecorded, BackupRecoveryTested, BackupVerified
from eaip.events.event import DomainEvent


class TestBackupRecorded:
    def test_defaults(self) -> None:
        e = BackupRecorded(record_id="b1", resource_id="res-1", backup_type="full", size_bytes=1024)
        assert e.event_type == "eaip.backupver.backup.recorded"
        assert isinstance(e, DomainEvent)

    def test_with_values(self) -> None:
        e = BackupRecorded(record_id="b1", resource_id="res-1", backup_type="full", size_bytes=1024)
        assert e.record_id == "b1"
        assert e.resource_id == "res-1"
        assert e.size_bytes == 1024

    def test_frozen(self) -> None:
        e = BackupRecorded(record_id="b1", resource_id="res-1", backup_type="full", size_bytes=1024)
        with pytest.raises((ValueError, TypeError)):
            e.record_id = "b2"  # type: ignore[misc]


class TestBackupVerified:
    def test_defaults(self) -> None:
        e = BackupVerified(record_id="b1", integrity_pass=True, duration_ms=100)
        assert e.event_type == "eaip.backupver.backup.verified"
        assert e.integrity_pass is True

    def test_with_values(self) -> None:
        e = BackupVerified(record_id="b1", integrity_pass=False, duration_ms=200)
        assert e.integrity_pass is False
        assert e.duration_ms == 200


class TestBackupRecoveryTested:
    def test_defaults(self) -> None:
        e = BackupRecoveryTested(record_id="b1", recovery_test_pass=True, duration_ms=500)
        assert e.event_type == "eaip.backupver.backup.recovery_tested"
        assert e.recovery_test_pass is True

    def test_with_values(self) -> None:
        e = BackupRecoveryTested(record_id="b1", recovery_test_pass=False, duration_ms=300)
        assert e.recovery_test_pass is False
        assert e.duration_ms == 300


class TestEventTypes:
    def test_all_have_unique_event_types(self) -> None:
        events = [BackupRecorded, BackupVerified, BackupRecoveryTested]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))
