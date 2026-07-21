"""Tests for BackupVerificationHealthCheck."""

from __future__ import annotations

import pytest

from eaip.backupver.health import BackupVerificationHealthCheck
from eaip.health.checks import HealthStatus


class TestBackupVerificationHealthCheck:
    @pytest.fixture
    def check(self) -> BackupVerificationHealthCheck:
        return BackupVerificationHealthCheck()

    def test_name(self, check: BackupVerificationHealthCheck) -> None:
        assert check.name == "backupver"

    async def test_healthy(self, check: BackupVerificationHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "backupver"
        assert "healthy" in report.message
