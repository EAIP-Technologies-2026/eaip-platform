"""Tests for EnvMgrHealthCheck."""

from __future__ import annotations

import pytest

from eaip.envmgr.health import EnvMgrHealthCheck
from eaip.health.checks import HealthStatus


class TestEnvMgrHealthCheck:
    @pytest.fixture
    def check(self) -> EnvMgrHealthCheck:
        return EnvMgrHealthCheck()

    def test_name(self, check: EnvMgrHealthCheck) -> None:
        assert check.name == "envmgr"

    async def test_healthy(self, check: EnvMgrHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "envmgr"
        assert "healthy" in report.message
