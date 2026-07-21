"""Tests for FirewallHealthCheck."""

from __future__ import annotations

import pytest

from eaip.firewall.health import FirewallHealthCheck
from eaip.health.checks import HealthStatus


class TestFirewallHealthCheck:
    @pytest.fixture
    def check(self) -> FirewallHealthCheck:
        return FirewallHealthCheck()

    def test_name(self, check: FirewallHealthCheck) -> None:
        assert check.name == "firewall"

    async def test_healthy(self, check: FirewallHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "firewall"
        assert "healthy" in report.message
