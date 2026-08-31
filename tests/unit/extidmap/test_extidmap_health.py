"""Tests for ExternalIdentityHealthCheck."""

from __future__ import annotations

import pytest

from eaip.extidmap.health import ExternalIdentityHealthCheck
from eaip.health.checks import HealthStatus


class TestExternalIdentityHealthCheck:
    @pytest.fixture
    def check(self) -> ExternalIdentityHealthCheck:
        return ExternalIdentityHealthCheck()

    def test_name(self, check: ExternalIdentityHealthCheck) -> None:
        assert check.name == "extidmap"

    async def test_healthy(self, check: ExternalIdentityHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "extidmap"
        assert "healthy" in report.message
