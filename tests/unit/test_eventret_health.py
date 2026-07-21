"""Tests for EventRetentionHealthCheck."""

from __future__ import annotations

import pytest

from eaip.eventret.health import EventRetentionHealthCheck
from eaip.health.checks import HealthStatus


class TestEventRetentionHealthCheck:
    @pytest.fixture
    def check(self) -> EventRetentionHealthCheck:
        return EventRetentionHealthCheck()

    def test_name(self, check: EventRetentionHealthCheck) -> None:
        assert check.name == "eventret"

    async def test_healthy(self, check: EventRetentionHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "eventret"
        assert "healthy" in report.message
