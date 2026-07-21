"""Tests for CliHealthCheck."""

from __future__ import annotations

from eaip.cli.health import CliHealthCheck
from eaip.health.checks import HealthCheck, HealthStatus


class TestCliHealthCheck:
    def test_is_health_check(self) -> None:
        assert isinstance(CliHealthCheck(), HealthCheck)

    def test_name(self) -> None:
        hc = CliHealthCheck()
        assert hc.name == "eaip.cli"

    async def test_check_healthy(self) -> None:
        hc = CliHealthCheck(registered_commands=3)
        report = await hc.check()
        assert report.status is HealthStatus.HEALTHY
        assert report.details["registered_commands"] == 3
        assert report.component == "Cli"

    async def test_check_degraded(self) -> None:
        hc = CliHealthCheck(registered_commands=0)
        report = await hc.check()
        assert report.status is HealthStatus.DEGRADED
        assert "no commands registered" in report.message
        assert report.details["registered_commands"] == 0

    async def test_commands_property(self) -> None:
        hc = CliHealthCheck()
        assert hc.registered_commands == 0
        hc.registered_commands = 5
        assert hc.registered_commands == 5
        report = await hc.check()
        assert report.details["registered_commands"] == 5
