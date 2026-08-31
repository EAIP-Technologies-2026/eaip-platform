"""Tests for ConfigDriftHealthCheck."""

from __future__ import annotations

import pytest

from eaip.configdrift.health import ConfigDriftHealthCheck
from eaip.health.checks import HealthStatus


class TestConfigDriftHealthCheck:
    @pytest.fixture
    def check(self) -> ConfigDriftHealthCheck:
        return ConfigDriftHealthCheck()

    def test_name(self, check: ConfigDriftHealthCheck) -> None:
        assert check.name == "configdrift"

    async def test_healthy(self, check: ConfigDriftHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "configdrift"
        assert "healthy" in report.message
