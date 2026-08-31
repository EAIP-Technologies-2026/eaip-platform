"""Tests for RetentionHealthCheck."""

from __future__ import annotations

import pytest

from eaip.health.checks import HealthStatus
from eaip.retention.health import RetentionHealthCheck


class TestRetentionHealthCheck:
    @pytest.fixture
    def check(self) -> RetentionHealthCheck:
        return RetentionHealthCheck()

    def test_name(self, check: RetentionHealthCheck) -> None:
        assert check.name == "retention"

    async def test_healthy(self, check: RetentionHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "retention"
        assert "healthy" in report.message
