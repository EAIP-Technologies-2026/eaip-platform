"""Tests for DataCatalog service."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.datacatalog.catalog import DataCatalog
from eaip.datacatalog.exceptions import AssetNotFoundError
from eaip.datacatalog.models import AssetType, CatalogConfig, DataAsset, DataSource


class TestDataCatalog:
    @pytest.fixture
    def catalog(self) -> DataCatalog:
        return DataCatalog()

    @pytest.fixture
    def sample_source(self) -> DataSource:
        return DataSource(id="src1", name="PostgreSQL", source_type="database")

    @pytest.fixture
    def sample_asset(self) -> DataAsset:
        return DataAsset(
            id="asset1",
            name="users_table",
            asset_type=AssetType.TABLE,
            source_id="src1",
            schema={"id": "integer", "name": "text"},
            tags=("pii", "customer"),
        )

    class TestRegisterSource:
        async def test_register_source(
            self, catalog: DataCatalog, sample_source: DataSource
        ) -> None:
            result = await catalog.register_source(sample_source)
            assert result.id == "src1"
            assert result.name == "PostgreSQL"

        async def test_list_sources(self, catalog: DataCatalog, sample_source: DataSource) -> None:
            await catalog.register_source(sample_source)
            sources = await catalog.list_sources()
            assert len(sources) == 1

    class TestRegisterAsset:
        async def test_register_asset(
            self, catalog: DataCatalog, sample_source: DataSource, sample_asset: DataAsset
        ) -> None:
            await catalog.register_source(sample_source)
            result = await catalog.register_asset(sample_asset)
            assert result.id == "asset1"
            assert result.name == "users_table"

        async def test_list_assets(
            self, catalog: DataCatalog, sample_source: DataSource, sample_asset: DataAsset
        ) -> None:
            await catalog.register_source(sample_source)
            await catalog.register_asset(sample_asset)
            assets = await catalog.list_assets()
            assert len(assets) == 1

    class TestGetAsset:
        async def test_get_asset(
            self, catalog: DataCatalog, sample_source: DataSource, sample_asset: DataAsset
        ) -> None:
            await catalog.register_source(sample_source)
            await catalog.register_asset(sample_asset)
            asset = await catalog.get_asset("asset1")
            assert asset.name == "users_table"

        async def test_get_asset_not_found(self, catalog: DataCatalog) -> None:
            with pytest.raises(AssetNotFoundError):
                await catalog.get_asset("nonexistent")

    class TestUpdateAsset:
        async def test_update_asset(
            self, catalog: DataCatalog, sample_source: DataSource, sample_asset: DataAsset
        ) -> None:
            await catalog.register_source(sample_source)
            await catalog.register_asset(sample_asset)
            updated = await catalog.update_asset("asset1", name="renamed_table")
            assert updated.name == "renamed_table"

        async def test_update_nonexistent(self, catalog: DataCatalog) -> None:
            with pytest.raises(AssetNotFoundError):
                await catalog.update_asset("nonexistent", name="new")

    class TestRemoveAsset:
        async def test_remove_asset(
            self, catalog: DataCatalog, sample_source: DataSource, sample_asset: DataAsset
        ) -> None:
            await catalog.register_source(sample_source)
            await catalog.register_asset(sample_asset)
            await catalog.remove_asset("asset1")
            assets = await catalog.list_assets()
            assert len(assets) == 0

        async def test_remove_nonexistent(self, catalog: DataCatalog) -> None:
            with pytest.raises(AssetNotFoundError):
                await catalog.remove_asset("nonexistent")

    class TestDiscoverByType:
        async def test_discover_by_type(
            self, catalog: DataCatalog, sample_source: DataSource, sample_asset: DataAsset
        ) -> None:
            await catalog.register_source(sample_source)
            await catalog.register_asset(sample_asset)
            tables = await catalog.discover_by_type(AssetType.TABLE)
            assert len(tables) == 1
            views = await catalog.discover_by_type(AssetType.VIEW)
            assert len(views) == 0

    class TestDiscoverBySource:
        async def test_discover_by_source(
            self, catalog: DataCatalog, sample_source: DataSource, sample_asset: DataAsset
        ) -> None:
            await catalog.register_source(sample_source)
            await catalog.register_asset(sample_asset)
            results = await catalog.discover_by_source("src1")
            assert len(results) == 1

        async def test_discover_by_source_empty(self, catalog: DataCatalog) -> None:
            results = await catalog.discover_by_source("unknown")
            assert results == []

    class TestSearch:
        async def test_search_by_name(
            self, catalog: DataCatalog, sample_source: DataSource, sample_asset: DataAsset
        ) -> None:
            await catalog.register_source(sample_source)
            await catalog.register_asset(sample_asset)
            results = await catalog.search("users")
            assert len(results) == 1

        async def test_search_no_results(
            self, catalog: DataCatalog, sample_source: DataSource, sample_asset: DataAsset
        ) -> None:
            await catalog.register_source(sample_source)
            await catalog.register_asset(sample_asset)
            results = await catalog.search("nonexistent")
            assert results == []

    class TestLineage:
        async def test_get_lineage(self, catalog: DataCatalog, sample_source: DataSource) -> None:
            await catalog.register_source(sample_source)
            parent = DataAsset(
                id="p1", name="raw_table", asset_type=AssetType.TABLE, source_id="src1"
            )
            child = DataAsset(
                id="c1",
                name="agg_view",
                asset_type=AssetType.VIEW,
                source_id="src1",
                lineage=("p1",),
            )
            await catalog.register_asset(parent)
            await catalog.register_asset(child)
            lineage = await catalog.get_lineage("c1")
            assert len(lineage) == 1
            assert lineage[0].id == "p1"

        async def test_get_lineage_no_parents(
            self, catalog: DataCatalog, sample_source: DataSource, sample_asset: DataAsset
        ) -> None:
            await catalog.register_source(sample_source)
            await catalog.register_asset(sample_asset)
            lineage = await catalog.get_lineage("asset1")
            assert lineage == []

    class TestConfig:
        def test_default_config(self) -> None:
            c = DataCatalog()
            assert c.config.auto_discovery_enabled is True
            assert c.config.discovery_interval_seconds == 86400

        def test_custom_config(self) -> None:
            config = CatalogConfig(auto_discovery_enabled=False, max_assets_per_source=500)
            c = DataCatalog(config=config)
            assert c.config.auto_discovery_enabled is False
            assert c.config.max_assets_per_source == 500


class TestDataAssetModels:
    def test_frozen(self) -> None:
        asset = DataAsset(id="a1", name="test", asset_type=AssetType.TABLE, source_id="s1")
        with pytest.raises(ValidationError):
            asset.name = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            DataAsset(
                id="a1", name="test", asset_type=AssetType.TABLE, source_id="s1", unknown=True
            )

    def test_schema_alias(self) -> None:
        asset = DataAsset(
            id="a1", name="test", asset_type=AssetType.TABLE, source_id="s1", schema={"col": "text"}
        )
        assert asset.schema_ == {"col": "text"}

    def test_defaults(self) -> None:
        asset = DataAsset(id="a1", name="test", asset_type=AssetType.FILE, source_id="s1")
        assert asset.tags == ()
        assert asset.lineage == ()
        assert asset.owner == ""
        assert asset.description == ""
