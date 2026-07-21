"""Tests for BlueGreenHealthCheck."""

from __future__ import annotations

import pytest

from eaip.bluegreen.health import BlueGreenHealthCheck
from eaip.health.checks import HealthStatus


class TestBlueGreenHealthCheck:
    @pytest.fixture
    def check(self) -> BlueGreenHealthCheck:
        return BlueGreenHealthCheck()

    def test_name(self, check: BlueGreenHealthCheck) -> None:
        assert check.name == "bluegreen"

    async def test_healthy(self, check: BlueGreenHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "bluegreen"
        assert "healthy" in report.message
