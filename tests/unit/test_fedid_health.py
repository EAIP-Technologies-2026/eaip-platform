"""Tests for FederatedIdentityHealthCheck."""

from __future__ import annotations

import pytest

from eaip.fedid.health import FederatedIdentityHealthCheck
from eaip.health.checks import HealthStatus


class TestFederatedIdentityHealthCheck:
    @pytest.fixture
    def check(self) -> FederatedIdentityHealthCheck:
        return FederatedIdentityHealthCheck()

    def test_name(self, check: FederatedIdentityHealthCheck) -> None:
        assert check.name == "fedid"

    async def test_healthy(self, check: FederatedIdentityHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "fedid"
        assert "healthy" in report.message
