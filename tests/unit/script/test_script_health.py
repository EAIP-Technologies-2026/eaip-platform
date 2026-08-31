"""Tests for ScriptHealthCheck."""

from __future__ import annotations

from eaip.health.checks import HealthStatus
from eaip.script.health import ScriptHealthCheck


class TestScriptHealthCheck:
    async def test_healthy_no_functions(self) -> None:
        check = ScriptHealthCheck()
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY
        assert report.component == "ScriptRuntime"

    async def test_healthy_with_functions(self) -> None:
        check = ScriptHealthCheck(registered_functions=5, active_executions=2)
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY

    async def test_degraded_timed_out(self) -> None:
        check = ScriptHealthCheck(registered_functions=10, timed_out_executions=1)
        report = await check.check()
        assert report.status is HealthStatus.DEGRADED

    async def test_degraded_many_failures(self) -> None:
        check = ScriptHealthCheck(registered_functions=10, failed_executions=6)
        report = await check.check()
        assert report.status is HealthStatus.DEGRADED

    async def test_healthy_few_failures(self) -> None:
        check = ScriptHealthCheck(registered_functions=10, failed_executions=3)
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY

    async def test_name_property(self) -> None:
        check = ScriptHealthCheck()
        assert check.name == "eaip.script"
