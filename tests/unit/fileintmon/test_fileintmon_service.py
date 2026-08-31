"""Tests for FileIntegrityMonitor."""

from __future__ import annotations

import pytest

from eaip.fileintmon.exceptions import FileNotFoundError
from eaip.fileintmon.models import FileStatus, MonitorConfig, MonitoredFile
from eaip.fileintmon.monitor import FileIntegrityMonitor


class TestFileIntegrityMonitor:
    @pytest.fixture
    def monitor(self) -> FileIntegrityMonitor:
        return FileIntegrityMonitor()

    @pytest.fixture
    def sample_file(self) -> MonitoredFile:
        return MonitoredFile(
            id="f1",
            path="/etc/config.yml",
            checksum_algorithm="sha256",
            baseline_hash="abc123",
            status=FileStatus.BASELINE,
        )

    class TestRecordBaseline:
        async def test_records_file(
            self, monitor: FileIntegrityMonitor, sample_file: MonitoredFile
        ) -> None:
            result = await monitor.record_baseline(sample_file)
            assert result.id == "f1"
            assert result.path == "/etc/config.yml"

        async def test_stores_file(
            self, monitor: FileIntegrityMonitor, sample_file: MonitoredFile
        ) -> None:
            await monitor.record_baseline(sample_file)
            stored = await monitor.get_monitored_file("f1")
            assert stored.baseline_hash == "abc123"

    class TestGetMonitoredFile:
        async def test_returns_file(
            self, monitor: FileIntegrityMonitor, sample_file: MonitoredFile
        ) -> None:
            await monitor.record_baseline(sample_file)
            result = await monitor.get_monitored_file("f1")
            assert result.checksum_algorithm == "sha256"

        async def test_raises_on_missing(self, monitor: FileIntegrityMonitor) -> None:
            with pytest.raises(FileNotFoundError):
                await monitor.get_monitored_file("nonexistent")

    class TestListMonitoredFiles:
        async def test_empty_when_none(self, monitor: FileIntegrityMonitor) -> None:
            assert await monitor.list_monitored_files() == []

        async def test_filters_by_status(
            self, monitor: FileIntegrityMonitor, sample_file: MonitoredFile
        ) -> None:
            f2 = MonitoredFile(id="f2", path="/etc/other.yml", status=FileStatus.CHANGED)
            await monitor.record_baseline(sample_file)
            await monitor.record_baseline(f2)
            result = await monitor.list_monitored_files(status=FileStatus.BASELINE)
            assert len(result) == 1

    class TestVerifyIntegrity:
        async def test_matching_hash(
            self, monitor: FileIntegrityMonitor, sample_file: MonitoredFile
        ) -> None:
            await monitor.record_baseline(sample_file)
            check = await monitor.verify_integrity("f1", "abc123")
            assert check.match is True

        async def test_mismatching_hash(
            self, monitor: FileIntegrityMonitor, sample_file: MonitoredFile
        ) -> None:
            await monitor.record_baseline(sample_file)
            check = await monitor.verify_integrity("f1", "wronghash")
            assert check.match is False

        async def test_raises_on_missing(self, monitor: FileIntegrityMonitor) -> None:
            with pytest.raises(FileNotFoundError):
                await monitor.verify_integrity("nonexistent", "hash")

        async def test_updates_status_on_mismatch(
            self, monitor: FileIntegrityMonitor, sample_file: MonitoredFile
        ) -> None:
            await monitor.record_baseline(sample_file)
            await monitor.verify_integrity("f1", "wronghash")
            mf = await monitor.get_monitored_file("f1")
            assert mf.status is FileStatus.CHANGED

    class TestMarkDeleted:
        async def test_marks_as_deleted(
            self, monitor: FileIntegrityMonitor, sample_file: MonitoredFile
        ) -> None:
            await monitor.record_baseline(sample_file)
            result = await monitor.mark_deleted("f1")
            assert result.status is FileStatus.DELETED

    class TestGetStatistics:
        async def test_returns_stats(
            self, monitor: FileIntegrityMonitor, sample_file: MonitoredFile
        ) -> None:
            await monitor.record_baseline(sample_file)
            await monitor.verify_integrity("f1", "abc123")
            stats = await monitor.get_statistics()
            assert stats["total_files"] == 1
            assert stats["baseline"] == 1

    class TestConfig:
        def test_default_config(self) -> None:
            m = FileIntegrityMonitor()
            assert m.config.checksum_algorithm == "sha256"

        def test_custom_config(self) -> None:
            cfg = MonitorConfig(checksum_algorithm="sha512")
            m = FileIntegrityMonitor(config=cfg)
            assert m.config.checksum_algorithm == "sha512"
