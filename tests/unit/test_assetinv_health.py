"""Tests for AssetInventoryHealthCheck."""

from __future__ import annotations

import pytest

from eaip.assetinv.health import AssetInventoryHealthCheck
from eaip.health.checks import HealthStatus


class TestAssetInventoryHealthCheck:
    @pytest.fixture
    def check(self) -> AssetInventoryHealthCheck:
        return AssetInventoryHealthCheck()

    def test_name(self, check: AssetInventoryHealthCheck) -> None:
        assert check.name == "assetinv"

    async def test_healthy(self, check: AssetInventoryHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "assetinv"
        assert "healthy" in report.message
