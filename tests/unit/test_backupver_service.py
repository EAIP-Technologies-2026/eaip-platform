"""Tests for BackupVerifier."""

from __future__ import annotations

import pytest

from eaip.backupver.exceptions import BackupNotFoundError
from eaip.backupver.models import BackupRecord, VerificationConfig
from eaip.backupver.verifier import BackupVerifier


class TestBackupVerifier:
    @pytest.fixture
    def verifier(self) -> BackupVerifier:
        return BackupVerifier()

    @pytest.fixture
    def sample_record(self) -> BackupRecord:
        return BackupRecord(
            id="b1",
            resource_id="res-1",
            backup_type="full",
            size_bytes=1024,
            checksum="abc123",
            location="/backups/res-1/full.bak",
        )

    class TestRecordBackup:
        async def test_records_backup(
            self, verifier: BackupVerifier, sample_record: BackupRecord
        ) -> None:
            result = await verifier.record_backup(sample_record)
            assert result.id == "b1"
            assert result.resource_id == "res-1"

        async def test_stores_record(
            self, verifier: BackupVerifier, sample_record: BackupRecord
        ) -> None:
            await verifier.record_backup(sample_record)
            stored = await verifier.get_record("b1")
            assert stored.id == "b1"

    class TestGetRecord:
        async def test_returns_record(
            self, verifier: BackupVerifier, sample_record: BackupRecord
        ) -> None:
            await verifier.record_backup(sample_record)
            result = await verifier.get_record("b1")
            assert result.size_bytes == 1024

        async def test_raises_on_missing(self, verifier: BackupVerifier) -> None:
            with pytest.raises(BackupNotFoundError):
                await verifier.get_record("nonexistent")

    class TestListRecords:
        async def test_empty_when_none(self, verifier: BackupVerifier) -> None:
            assert await verifier.list_records() == []

        async def test_returns_all(
            self, verifier: BackupVerifier, sample_record: BackupRecord
        ) -> None:
            await verifier.record_backup(sample_record)
            records = await verifier.list_records()
            assert len(records) == 1

        async def test_filters_by_resource(self, verifier: BackupVerifier) -> None:
            b1 = BackupRecord(id="b1", resource_id="res-1", backup_type="full")
            b2 = BackupRecord(id="b2", resource_id="res-2", backup_type="incr")
            await verifier.record_backup(b1)
            await verifier.record_backup(b2)
            result = await verifier.list_records(resource_id="res-1")
            assert len(result) == 1
            assert result[0].id == "b1"

        async def test_filters_by_verified(self, verifier: BackupVerifier) -> None:
            b1 = BackupRecord(id="b1", resource_id="res-1", backup_type="full")
            b2 = BackupRecord(id="b2", resource_id="res-2", backup_type="full", verified=True)
            await verifier.record_backup(b1)
            await verifier.record_backup(b2)
            result = await verifier.list_records(verified=True)
            assert len(result) == 1

    class TestVerifyBackup:
        async def test_verifies_backup(
            self, verifier: BackupVerifier, sample_record: BackupRecord
        ) -> None:
            await verifier.record_backup(sample_record)
            result = await verifier.verify_backup("b1")
            assert result.record_id == "b1"
            assert result.verified is True

        async def test_raises_on_missing(self, verifier: BackupVerifier) -> None:
            with pytest.raises(BackupNotFoundError):
                await verifier.verify_backup("nonexistent")

        async def test_updates_record(
            self, verifier: BackupVerifier, sample_record: BackupRecord
        ) -> None:
            await verifier.record_backup(sample_record)
            await verifier.verify_backup("b1")
            record = await verifier.get_record("b1")
            assert record.verified is True

    class TestTestRecovery:
        async def test_tests_recovery(
            self, verifier: BackupVerifier, sample_record: BackupRecord
        ) -> None:
            await verifier.record_backup(sample_record)
            result = await verifier.test_recovery("b1")
            assert result.record_id == "b1"

        async def test_raises_on_missing(self, verifier: BackupVerifier) -> None:
            with pytest.raises(BackupNotFoundError):
                await verifier.test_recovery("nonexistent")

    class TestGetStatistics:
        async def test_returns_stats(
            self, verifier: BackupVerifier, sample_record: BackupRecord
        ) -> None:
            await verifier.record_backup(sample_record)
            stats = await verifier.get_statistics()
            assert stats["total_records"] == 1
            assert stats["total_size_bytes"] == 1024

    class TestConfig:
        def test_default_config(self) -> None:
            v = BackupVerifier()
            assert v.config.checksum_algorithm == "sha256"

        def test_custom_config(self) -> None:
            cfg = VerificationConfig(checksum_algorithm="sha512")
            v = BackupVerifier(config=cfg)
            assert v.config.checksum_algorithm == "sha512"
