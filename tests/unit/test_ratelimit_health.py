"""Tests for RateLimitHealthCheck."""

from __future__ import annotations

import pytest

from eaip.health.checks import HealthStatus
from eaip.ratelimit.health import RateLimitHealthCheck


class TestRateLimitHealthCheck:
    @pytest.fixture
    def check(self) -> RateLimitHealthCheck:
        return RateLimitHealthCheck()

    def test_name(self, check: RateLimitHealthCheck) -> None:
        assert check.name == "ratelimit"

    async def test_healthy(self, check: RateLimitHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "ratelimit"
        assert "healthy" in report.message
