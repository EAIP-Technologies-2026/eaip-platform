"""Tests for CapacityAnalyzerHealthCheck."""

from __future__ import annotations

import pytest

from eaip.capacity.health import CapacityAnalyzerHealthCheck
from eaip.health.checks import HealthStatus


class TestCapacityAnalyzerHealthCheck:
    @pytest.fixture
    def check(self) -> CapacityAnalyzerHealthCheck:
        return CapacityAnalyzerHealthCheck()

    def test_name(self, check: CapacityAnalyzerHealthCheck) -> None:
        assert check.name == "capacity"

    async def test_healthy(self, check: CapacityAnalyzerHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "capacity"
        assert "healthy" in report.message
