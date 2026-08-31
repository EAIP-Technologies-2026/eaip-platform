"""Tests for CloudManagerHealthCheck."""

from __future__ import annotations

import pytest

from eaip.cloudmgr.health import CloudManagerHealthCheck
from eaip.health.checks import HealthStatus


class TestCloudManagerHealthCheck:
    @pytest.fixture
    def check(self) -> CloudManagerHealthCheck:
        return CloudManagerHealthCheck()

    def test_name(self, check: CloudManagerHealthCheck) -> None:
        assert check.name == "cloudmgr"

    async def test_healthy(self, check: CloudManagerHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "cloudmgr"
        assert "healthy" in report.message
