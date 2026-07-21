"""Tests for ExportComplianceHealthCheck."""

from __future__ import annotations

import pytest

from eaip.exportcheck.health import ExportComplianceHealthCheck
from eaip.health.checks import HealthStatus


class TestExportComplianceHealthCheck:
    @pytest.fixture
    def check(self) -> ExportComplianceHealthCheck:
        return ExportComplianceHealthCheck()

    def test_name(self, check: ExportComplianceHealthCheck) -> None:
        assert check.name == "exportcheck"

    async def test_healthy(self, check: ExportComplianceHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "exportcheck"
        assert "healthy" in report.message
