"""Tests for CalendarHealthCheck."""

from __future__ import annotations

import pytest

from eaip.bcalendar.health import CalendarHealthCheck
from eaip.health.checks import HealthStatus


class TestCalendarHealthCheck:
    @pytest.fixture
    def check(self) -> CalendarHealthCheck:
        return CalendarHealthCheck()

    def test_name(self, check: CalendarHealthCheck) -> None:
        assert check.name == "bcalendar"

    async def test_healthy(self, check: CalendarHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "bcalendar"
        assert "healthy" in report.message
