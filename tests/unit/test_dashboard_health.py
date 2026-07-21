"""Tests for DashboardHealthCheck."""

from __future__ import annotations

import pytest

from eaip.dashboard.health import DashboardHealthCheck
from eaip.health.checks import HealthStatus


class TestDashboardHealthCheck:
    @pytest.fixture
    def check(self) -> DashboardHealthCheck:
        return DashboardHealthCheck()

    def test_name(self, check: DashboardHealthCheck) -> None:
        assert check.name == "dashboard"

    async def test_healthy(self, check: DashboardHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "dashboard"
        assert "healthy" in report.message
