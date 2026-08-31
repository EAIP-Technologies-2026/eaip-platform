"""Tests for Agent Runtime health check."""

from __future__ import annotations

from eaip.agents.health import AgentHealthCheck
from eaip.health.checks import HealthReport, HealthStatus


class _FakeRuntime:
    async def health(self) -> object:
        return HealthReport(
            component="agent_runtime",
            status=HealthStatus.HEALTHY,
            message="ok",
        )


class TestAgentHealthCheck:
    async def test_health_check_healthy(self) -> None:
        check = AgentHealthCheck(_FakeRuntime())
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY
        assert "agent" in report.component.lower()

    async def test_returns_expected_structure(self) -> None:
        check = AgentHealthCheck(_FakeRuntime())
        report = await check.check()
        statuses = (HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY)
        assert report.status in statuses
        assert isinstance(report.message, str)
        assert len(report.message) > 0
