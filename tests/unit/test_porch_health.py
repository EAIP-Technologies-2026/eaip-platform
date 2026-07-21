"""Tests for PorchHealthCheck."""

from __future__ import annotations

import pytest

from eaip.health.checks import HealthStatus
from eaip.porch.health import PorchHealthCheck


class TestPorchHealthCheck:
    @pytest.fixture
    def check(self) -> PorchHealthCheck:
        return PorchHealthCheck()

    def test_name(self, check: PorchHealthCheck) -> None:
        assert check.name == "porch"

    async def test_healthy(self, check: PorchHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "porch"
        assert "healthy" in report.message
