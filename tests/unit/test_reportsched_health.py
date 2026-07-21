"""Tests for ReportSchedulerHealthCheck."""

from __future__ import annotations

import pytest

from eaip.health.checks import HealthStatus
from eaip.reportsched.health import ReportSchedulerHealthCheck


class TestReportSchedulerHealthCheck:
    @pytest.fixture
    def check(self) -> ReportSchedulerHealthCheck:
        return ReportSchedulerHealthCheck()

    def test_name(self, check: ReportSchedulerHealthCheck) -> None:
        assert check.name == "reportsched"

    async def test_healthy(self, check: ReportSchedulerHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "reportsched"
        assert "healthy" in report.message
