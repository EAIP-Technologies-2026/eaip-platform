"""Tests for DataSyncHealthCheck."""

from __future__ import annotations

import pytest

from eaip.datasync.health import DataSyncHealthCheck
from eaip.health.checks import HealthStatus


class TestDataSyncHealthCheck:
    @pytest.fixture
    def check(self) -> DataSyncHealthCheck:
        return DataSyncHealthCheck()

    def test_name(self, check: DataSyncHealthCheck) -> None:
        assert check.name == "datasync"

    async def test_healthy(self, check: DataSyncHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "datasync"
        assert "healthy" in report.message
