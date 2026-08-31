"""Tests for EndpointSecurityHealthCheck."""

from __future__ import annotations

import pytest

from eaip.endpointsec.health import EndpointSecurityHealthCheck
from eaip.health.checks import HealthStatus


class TestEndpointSecurityHealthCheck:
    @pytest.fixture
    def check(self) -> EndpointSecurityHealthCheck:
        return EndpointSecurityHealthCheck()

    def test_name(self, check: EndpointSecurityHealthCheck) -> None:
        assert check.name == "endpointsec"

    async def test_healthy(self, check: EndpointSecurityHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "endpointsec"
        assert "healthy" in report.message
