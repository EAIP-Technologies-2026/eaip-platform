"""Tests for BatchJobSchedulerHealthCheck."""

from __future__ import annotations

import pytest

from eaip.batchjob.health import BatchJobSchedulerHealthCheck
from eaip.health.checks import HealthStatus


class TestBatchJobSchedulerHealthCheck:
    @pytest.fixture
    def check(self) -> BatchJobSchedulerHealthCheck:
        return BatchJobSchedulerHealthCheck()

    def test_name(self, check: BatchJobSchedulerHealthCheck) -> None:
        assert check.name == "batchjob"

    async def test_healthy(self, check: BatchJobSchedulerHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "batchjob"
        assert "healthy" in report.message
