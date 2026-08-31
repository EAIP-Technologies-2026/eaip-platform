"""Tests for AssetInventory."""

from __future__ import annotations

import pytest

from eaip.assetinv.exceptions import AssetNotFoundError
from eaip.assetinv.models import Asset, AssetStatus, InventoryConfig
from eaip.assetinv.service import AssetInventory


class TestAssetInventory:
    @pytest.fixture
    def service(self) -> AssetInventory:
        return AssetInventory()

    @pytest.fixture
    def sample_asset(self) -> Asset:
        return Asset(id="a1", name="Laptop", type="hardware", department="IT", current_value=1500.0)

    class TestRegisterAsset:
        async def test_registers_asset(self, service: AssetInventory, sample_asset: Asset) -> None:
            result = await service.register_asset(sample_asset)
            assert result.id == "a1"
            assert result.name == "Laptop"

        async def test_stores_asset(self, service: AssetInventory, sample_asset: Asset) -> None:
            await service.register_asset(sample_asset)
            stored = await service.get_asset("a1")
            assert stored.id == "a1"

    class TestGetAsset:
        async def test_returns_asset(self, service: AssetInventory, sample_asset: Asset) -> None:
            await service.register_asset(sample_asset)
            result = await service.get_asset("a1")
            assert result.name == "Laptop"

        async def test_raises_on_missing(self, service: AssetInventory) -> None:
            with pytest.raises(AssetNotFoundError):
                await service.get_asset("nonexistent")

    class TestUpdateAsset:
        async def test_updates_asset(self, service: AssetInventory, sample_asset: Asset) -> None:
            await service.register_asset(sample_asset)
            updated = await service.update_asset("a1", name="Updated Laptop")
            assert updated.name == "Updated Laptop"

        async def test_raises_on_missing(self, service: AssetInventory) -> None:
            with pytest.raises(AssetNotFoundError):
                await service.update_asset("nonexistent", name="Test")

    class TestListAssets:
        async def test_empty_when_none(self, service: AssetInventory) -> None:
            assert await service.list_assets() == []

        async def test_returns_all(self, service: AssetInventory, sample_asset: Asset) -> None:
            await service.register_asset(sample_asset)
            assets = await service.list_assets()
            assert len(assets) == 1

        async def test_filters_by_status(self, service: AssetInventory) -> None:
            a1 = Asset(id="a1", name="A", type="t", status=AssetStatus.ACTIVE)
            a2 = Asset(id="a2", name="B", type="t", status=AssetStatus.DECOMMISSIONED)
            await service.register_asset(a1)
            await service.register_asset(a2)
            result = await service.list_assets(status=AssetStatus.ACTIVE)
            assert len(result) == 1
            assert result[0].id == "a1"

        async def test_filters_by_department(self, service: AssetInventory) -> None:
            a1 = Asset(id="a1", name="A", type="t", department="IT")
            a2 = Asset(id="a2", name="B", type="t", department="HR")
            await service.register_asset(a1)
            await service.register_asset(a2)
            result = await service.list_assets(department="IT")
            assert len(result) == 1

    class TestDecommissionAsset:
        async def test_decommissions_asset(
            self, service: AssetInventory, sample_asset: Asset
        ) -> None:
            await service.register_asset(sample_asset)
            result = await service.decommission_asset("a1", reason="end of life")
            assert result.status == AssetStatus.DECOMMISSIONED

        async def test_raises_on_missing(self, service: AssetInventory) -> None:
            with pytest.raises(AssetNotFoundError):
                await service.decommission_asset("nonexistent")

    class TestGetStatistics:
        async def test_returns_stats(self, service: AssetInventory, sample_asset: Asset) -> None:
            await service.register_asset(sample_asset)
            stats = await service.get_statistics()
            assert stats["total_assets"] == 1
            assert stats["total_value"] == 1500.0

    class TestConfig:
        def test_default_config(self) -> None:
            svc = AssetInventory()
            assert svc.config.default_department == "general"

        def test_custom_config(self) -> None:
            cfg = InventoryConfig(default_department="IT")
            svc = AssetInventory(config=cfg)
            assert svc.config.default_department == "IT"
