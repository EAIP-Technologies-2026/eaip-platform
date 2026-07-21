"""Tests for AlertCorrelationHealthCheck."""

from __future__ import annotations

import pytest

from eaip.alertcorr.health import AlertCorrelationHealthCheck
from eaip.health.checks import HealthStatus


class TestAlertCorrelationHealthCheck:
    @pytest.fixture
    def check(self) -> AlertCorrelationHealthCheck:
        return AlertCorrelationHealthCheck()

    def test_name(self, check: AlertCorrelationHealthCheck) -> None:
        assert check.name == "alertcorr"

    async def test_healthy(self, check: AlertCorrelationHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "alertcorr"
        assert "healthy" in report.message
