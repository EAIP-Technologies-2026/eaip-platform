"""Tests for ArchiveHealthCheck."""

from __future__ import annotations

import pytest

from eaip.archive.health import ArchiveHealthCheck
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class TestArchiveHealthCheck:
    def test_protocol(self) -> None:
        check = ArchiveHealthCheck()
        assert isinstance(check, HealthCheck)
        assert check.name == "eaip.archive"

    @pytest.mark.asyncio
    async def test_healthy_by_default(self) -> None:
        check = ArchiveHealthCheck()
        check._total_archives = 10
        check._total_size_bytes = 1024
        report = await check.check()
        assert isinstance(report, HealthReport)

    @pytest.mark.asyncio
    async def test_healthy_no_pending(self) -> None:
        check = ArchiveHealthCheck(
            total_archives=5,
            total_size_bytes=5000,
            pending_cleanups=0,
        )
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY
        assert report.component == "Archive"
        assert report.details["total_archives"] == 5
        assert report.details["total_size_bytes"] == 5000
        assert report.details["pending_cleanups"] == 0

    @pytest.mark.asyncio
    async def test_degraded_with_pending_cleanups(self) -> None:
        check = ArchiveHealthCheck(
            total_archives=5,
            total_size_bytes=5000,
            pending_cleanups=2,
        )
        report = await check.check()
        assert report.status is HealthStatus.DEGRADED
        assert "pending cleanup" in report.message

    @pytest.mark.asyncio
    async def test_details_accuracy(self) -> None:
        check = ArchiveHealthCheck(
            total_archives=42,
            total_size_bytes=1048576,
        )
        report = await check.check()
        assert report.details["total_archives"] == 42
        assert report.details["total_size_bytes"] == 1048576
