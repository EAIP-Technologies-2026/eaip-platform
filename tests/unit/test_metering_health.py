"""Tests for MeteringHealthCheck."""

from __future__ import annotations

import pytest

from eaip.health.checks import HealthStatus
from eaip.metering.health import MeteringHealthCheck


class TestMeteringHealthCheck:
    @pytest.fixture
    def check(self) -> MeteringHealthCheck:
        return MeteringHealthCheck()

    def test_name(self, check: MeteringHealthCheck) -> None:
        assert check.name == "metering"

    async def test_healthy(self, check: MeteringHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "metering"
        assert "healthy" in report.message
