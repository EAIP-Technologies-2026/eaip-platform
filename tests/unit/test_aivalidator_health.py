"""Tests for AIValidatorHealthCheck."""

from __future__ import annotations

import pytest

from eaip.aivalidator.health import AIValidatorHealthCheck
from eaip.health.checks import HealthStatus


class TestAIValidatorHealthCheck:
    @pytest.fixture
    def check(self) -> AIValidatorHealthCheck:
        return AIValidatorHealthCheck()

    def test_name(self, check: AIValidatorHealthCheck) -> None:
        assert check.name == "aivalidator"

    async def test_healthy(self, check: AIValidatorHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "aivalidator"
        assert "healthy" in report.message
