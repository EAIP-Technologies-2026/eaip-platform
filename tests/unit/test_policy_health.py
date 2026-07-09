from __future__ import annotations

import asyncio

from eaip.health.checks import HealthStatus
from eaip.policy.health import PolicyHealthCheck
from eaip.policy.models import Policy
from eaip.policy.registry import PolicyRegistry


class TestPolicyHealthCheck:
    def test_no_policies_healthy(self) -> None:
        registry = PolicyRegistry()
        check = PolicyHealthCheck(registry)
        report = asyncio.run(check.check())
        assert report.status is HealthStatus.HEALTHY
        assert report.component == "policy"

    def test_all_enabled_healthy(self) -> None:
        registry = PolicyRegistry()
        registry.register(Policy(id="p1", name="p1"))
        registry.register(Policy(id="p2", name="p2"))
        check = PolicyHealthCheck(registry)
        report = asyncio.run(check.check())
        assert report.status is HealthStatus.HEALTHY

    def test_some_disabled_degraded(self) -> None:
        registry = PolicyRegistry()
        registry.register(Policy(id="p1", name="p1"))
        registry.register(Policy(id="p2", name="p2", enabled=False))
        check = PolicyHealthCheck(registry)
        report = asyncio.run(check.check())
        assert report.status is HealthStatus.DEGRADED
        assert "disabled" in report.message

    def test_details_contains_counts(self) -> None:
        registry = PolicyRegistry()
        registry.register(Policy(id="p1", name="p1"))
        registry.register(Policy(id="p2", name="p2", enabled=False))
        check = PolicyHealthCheck(registry)
        report = asyncio.run(check.check())
        assert report.details["total"] == 2
        assert report.details["enabled"] == 1
        assert report.details["disabled"] == 1
