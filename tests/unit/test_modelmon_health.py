"""Tests for ModelMonitorHealthCheck."""

from __future__ import annotations

import pytest

from eaip.health.checks import HealthStatus
from eaip.modelmon.health import ModelMonitorHealthCheck


class TestModelMonitorHealthCheck:
    @pytest.fixture
    def check(self) -> ModelMonitorHealthCheck:
        return ModelMonitorHealthCheck()

    def test_name(self, check: ModelMonitorHealthCheck) -> None:
        assert check.name == "modelmon"

    async def test_healthy(self, check: ModelMonitorHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "modelmon"
        assert "healthy" in report.message
