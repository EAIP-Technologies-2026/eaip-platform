"""Tests for RollbackManagerHealthCheck."""

from __future__ import annotations

import pytest

from eaip.health.checks import HealthStatus
from eaip.rollbackmgr.health import RollbackManagerHealthCheck


class TestRollbackManagerHealthCheck:
    @pytest.fixture
    def check(self) -> RollbackManagerHealthCheck:
        return RollbackManagerHealthCheck()

    def test_name(self, check: RollbackManagerHealthCheck) -> None:
        assert check.name == "rollbackmgr"

    async def test_healthy(self, check: RollbackManagerHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "rollbackmgr"
        assert "healthy" in report.message
