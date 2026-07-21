"""Tests for BootstrapHealthCheck."""

from __future__ import annotations

from eaip.bootstrap.health import BootstrapHealthCheck
from eaip.health.checks import HealthStatus


class TestBootstrapHealthCheck:
    async def test_healthy_with_templates(self) -> None:
        check = BootstrapHealthCheck(available_templates=5, total_scaffolds=10)
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY

    async def test_degraded_no_templates(self) -> None:
        check = BootstrapHealthCheck()
        report = await check.check()
        assert report.status is HealthStatus.DEGRADED
        assert "no project templates" in report.message

    async def test_details(self) -> None:
        check = BootstrapHealthCheck(available_templates=3, total_scaffolds=7)
        report = await check.check()
        assert report.details["available_templates"] == 3
        assert report.details["total_scaffolds"] == 7

    async def test_name_property(self) -> None:
        check = BootstrapHealthCheck()
        assert check.name == "eaip.bootstrap"
