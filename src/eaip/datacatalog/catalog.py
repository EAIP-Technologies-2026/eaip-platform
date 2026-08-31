"""DataCatalog — registers data assets, discovers by type/source, searches, and tracks lineage."""

from __future__ import annotations

from eaip.datacatalog.events import AssetRegistered, AssetRemoved, AssetUpdated
from eaip.datacatalog.exceptions import AssetNotFoundError
from eaip.datacatalog.models import AssetType, CatalogConfig, DataAsset, DataSource
from eaip.logging.context import get_logger


class DataCatalog:
    """Central service for managing the enterprise data catalog."""

    def __init__(self, config: CatalogConfig | None = None) -> None:
        self._config = config or CatalogConfig()
        self._assets: dict[str, DataAsset] = {}
        self._sources: dict[str, DataSource] = {}
        self._log = get_logger("eaip.datacatalog.catalog")

    @property
    def config(self) -> CatalogConfig:
        return self._config

    async def register_source(self, source: DataSource) -> DataSource:
        """Register a new data source."""
        self._sources[source.id] = source
        self._log.info("datacatalog.source.registered", source_id=source.id, name=source.name)
        return source

    async def register_asset(self, asset: DataAsset) -> DataAsset:
        """Register a new data asset in the catalog."""
        self._assets[asset.id] = asset
        event = AssetRegistered(
            asset_id=asset.id,
            name=asset.name,
            asset_type=asset.asset_type.value,
            source_id=asset.source_id,
        )
        self._log.info("datacatalog.asset.registered", asset_id=asset.id, name=asset.name)
        return asset

    async def update_asset(self, asset_id: str, **updates: str) -> DataAsset:
        """Update an existing data asset."""
        existing = self._assets.get(asset_id)
        if existing is None:
            raise AssetNotFoundError(f"Asset '{asset_id}' not found")

        updated = existing.model_copy(update=updates, deep=True)
        self._assets[asset_id] = updated
        event = AssetUpdated(asset_id=asset_id, name=updated.name, changes=dict(updates))
        self._log.info("datacatalog.asset.updated", asset_id=asset_id)
        return updated

    async def remove_asset(self, asset_id: str, reason: str = "") -> None:
        """Remove a data asset from the catalog."""
        asset = self._assets.pop(asset_id, None)
        if asset is None:
            raise AssetNotFoundError(f"Asset '{asset_id}' not found")
        event = AssetRemoved(asset_id=asset_id, name=asset.name, reason=reason)
        self._log.info("datacatalog.asset.removed", asset_id=asset_id)

    async def get_asset(self, asset_id: str) -> DataAsset:
        """Retrieve a data asset by ID."""
        asset = self._assets.get(asset_id)
        if asset is None:
            raise AssetNotFoundError(f"Asset '{asset_id}' not found")
        return asset

    async def discover_by_type(self, asset_type: AssetType) -> list[DataAsset]:
        """Discover all assets of a given type."""
        return [a for a in self._assets.values() if a.asset_type == asset_type]

    async def discover_by_source(self, source_id: str) -> list[DataAsset]:
        """Discover all assets originating from a given source."""
        return [a for a in self._assets.values() if a.source_id == source_id]

    async def search(self, query: str) -> list[DataAsset]:
        """Search for assets by name or description."""
        q = query.lower()
        return [
            a for a in self._assets.values() if q in a.name.lower() or q in a.description.lower()
        ]

    async def get_lineage(self, asset_id: str) -> list[DataAsset]:
        """Retrieve the lineage chain for a data asset."""
        asset = await self.get_asset(asset_id)
        lineage: list[DataAsset] = []
        for parent_id in asset.lineage:
            parent = self._assets.get(parent_id)
            if parent is not None:
                lineage.append(parent)
        return lineage

    async def list_assets(self) -> list[DataAsset]:
        """List all registered data assets."""
        return list(self._assets.values())

    async def list_sources(self) -> list[DataSource]:
        """List all registered data sources."""
        return list(self._sources.values())


__all__ = ["DataCatalog"]
