"""Tests for SkillRegistryHealthCheck."""

from __future__ import annotations

import pytest

from eaip.health.checks import HealthStatus
from eaip.skillreg.health import SkillRegistryHealthCheck


class TestSkillRegistryHealthCheck:
    @pytest.fixture
    def check(self) -> SkillRegistryHealthCheck:
        return SkillRegistryHealthCheck()

    def test_name(self, check: SkillRegistryHealthCheck) -> None:
        assert check.name == "skillreg"

    async def test_healthy(self, check: SkillRegistryHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "skillreg"
        assert "healthy" in report.message
