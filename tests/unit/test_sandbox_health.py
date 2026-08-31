"""Tests for SandboxHealthCheck."""

from __future__ import annotations

import pytest

from eaip.health.checks import HealthStatus
from eaip.sandbox.health import SandboxHealthCheck


class TestSandboxHealthCheck:
    @pytest.fixture
    def check(self) -> SandboxHealthCheck:
        return SandboxHealthCheck()

    def test_name(self, check: SandboxHealthCheck) -> None:
        assert check.name == "sandbox"

    async def test_healthy(self, check: SandboxHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "sandbox"
        assert "healthy" in report.message
