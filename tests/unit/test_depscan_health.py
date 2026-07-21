"""Tests for DependencyScannerHealthCheck."""

from __future__ import annotations

import pytest

from eaip.depscan.health import DependencyScannerHealthCheck
from eaip.health.checks import HealthStatus


class TestDependencyScannerHealthCheck:
    @pytest.fixture
    def check(self) -> DependencyScannerHealthCheck:
        return DependencyScannerHealthCheck()

    def test_name(self, check: DependencyScannerHealthCheck) -> None:
        assert check.name == "depscan"

    async def test_healthy(self, check: DependencyScannerHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "depscan"
        assert "healthy" in report.message
