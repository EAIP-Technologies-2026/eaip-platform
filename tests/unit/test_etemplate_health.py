"""Tests for TemplateEngineHealthCheck."""

from __future__ import annotations

import pytest

from eaip.etemplate.health import TemplateEngineHealthCheck
from eaip.health.checks import HealthStatus


class TestTemplateEngineHealthCheck:
    @pytest.fixture
    def check(self) -> TemplateEngineHealthCheck:
        return TemplateEngineHealthCheck()

    def test_name(self, check: TemplateEngineHealthCheck) -> None:
        assert check.name == "etemplate"

    async def test_healthy(self, check: TemplateEngineHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "etemplate"
        assert "healthy" in report.message
