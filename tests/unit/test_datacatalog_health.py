"""Tests for DataCatalogHealthCheck."""

from __future__ import annotations

import pytest

from eaip.datacatalog.health import DataCatalogHealthCheck
from eaip.health.checks import HealthStatus


class TestDataCatalogHealthCheck:
    @pytest.fixture
    def check(self) -> DataCatalogHealthCheck:
        return DataCatalogHealthCheck()

    def test_name(self, check: DataCatalogHealthCheck) -> None:
        assert check.name == "datacatalog"

    async def test_healthy(self, check: DataCatalogHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "datacatalog"
        assert "healthy" in report.message
