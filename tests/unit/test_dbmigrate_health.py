"""Tests for DatabaseMigrationHealthCheck."""

from __future__ import annotations

import pytest

from eaip.dbmigrate.health import DatabaseMigrationHealthCheck
from eaip.health.checks import HealthStatus


class TestDatabaseMigrationHealthCheck:
    @pytest.fixture
    def check(self) -> DatabaseMigrationHealthCheck:
        return DatabaseMigrationHealthCheck()

    def test_name(self, check: DatabaseMigrationHealthCheck) -> None:
        assert check.name == "dbmigrate"

    async def test_healthy(self, check: DatabaseMigrationHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "dbmigrate"
        assert "healthy" in report.message
