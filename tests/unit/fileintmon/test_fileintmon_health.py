"""Tests for FileIntegrityHealthCheck."""

from __future__ import annotations

import pytest

from eaip.fileintmon.health import FileIntegrityHealthCheck
from eaip.health.checks import HealthStatus


class TestFileIntegrityHealthCheck:
    @pytest.fixture
    def check(self) -> FileIntegrityHealthCheck:
        return FileIntegrityHealthCheck()

    def test_name(self, check: FileIntegrityHealthCheck) -> None:
        assert check.name == "fileintmon"

    async def test_healthy(self, check: FileIntegrityHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "fileintmon"
        assert "healthy" in report.message
