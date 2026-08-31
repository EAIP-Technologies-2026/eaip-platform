"""Tests for CacheInvalidationHealthCheck."""

from __future__ import annotations

import pytest

from eaip.cacheinv.health import CacheInvalidationHealthCheck
from eaip.health.checks import HealthStatus


class TestCacheInvalidationHealthCheck:
    @pytest.fixture
    def check(self) -> CacheInvalidationHealthCheck:
        return CacheInvalidationHealthCheck()

    def test_name(self, check: CacheInvalidationHealthCheck) -> None:
        assert check.name == "cacheinv"

    async def test_healthy(self, check: CacheInvalidationHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "cacheinv"
        assert "healthy" in report.message
