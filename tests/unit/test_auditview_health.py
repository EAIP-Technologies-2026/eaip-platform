"""Tests for AuditViewHealthCheck."""

from __future__ import annotations

import pytest

from eaip.auditview.health import AuditViewHealthCheck
from eaip.health.checks import HealthStatus


class TestAuditViewHealthCheck:
    @pytest.fixture
    def check(self) -> AuditViewHealthCheck:
        return AuditViewHealthCheck()

    def test_name(self, check: AuditViewHealthCheck) -> None:
        assert check.name == "auditview"

    async def test_healthy(self, check: AuditViewHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "auditview"
        assert "healthy" in report.message
