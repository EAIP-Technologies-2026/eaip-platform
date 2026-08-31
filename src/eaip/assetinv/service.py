"""AssetInventory — register, update, decommission, and query assets."""

from __future__ import annotations

from eaip.assetinv.events import AssetDecommissioned, AssetRegistered, AssetUpdated
from eaip.assetinv.exceptions import AssetNotFoundError
from eaip.assetinv.models import Asset, AssetStatus, InventoryConfig
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class AssetInventory:
    """Central service for managing the asset lifecycle."""

    def __init__(self, config: InventoryConfig | None = None) -> None:
        self._config = config or InventoryConfig()
        self._assets: dict[str, Asset] = {}
        self._log = get_logger("eaip.assetinv.service")

    @property
    def config(self) -> InventoryConfig:
        return self._config

    async def register_asset(self, asset: Asset) -> Asset:
        """Register a new asset in the inventory."""
        self._assets[asset.id] = asset
        AssetRegistered(
            asset_id=asset.id,
            name=asset.name,
            asset_type=asset.type,
            department=asset.department,
        )
        self._log.info("assetinv.asset.registered", asset_id=asset.id, name=asset.name)
        return asset

    async def update_asset(self, asset_id: str, **changes: object) -> Asset:
        """Update an existing asset's attributes."""
        asset = self._assets.get(asset_id)
        if asset is None:
            raise AssetNotFoundError(f"Asset not found: {asset_id}")
        updated = asset.model_copy(update={"updated_at": utc_now(), **changes})
        self._assets[asset_id] = updated
        AssetUpdated(asset_id=asset_id, changes={k: v for k, v in changes.items()})
        self._log.info("assetinv.asset.updated", asset_id=asset_id)
        return updated

    async def get_asset(self, asset_id: str) -> Asset:
        """Get an asset by ID."""
        asset = self._assets.get(asset_id)
        if asset is None:
            raise AssetNotFoundError(f"Asset not found: {asset_id}")
        return asset

    async def list_assets(
        self,
        status: AssetStatus | None = None,
        department: str | None = None,
        category: str | None = None,
    ) -> list[Asset]:
        """List all assets, optionally filtered by status, department, or category."""
        result: list[Asset] = list(self._assets.values())
        if status is not None:
            result = [a for a in result if a.status == status]
        if department is not None:
            result = [a for a in result if a.department == department]
        if category is not None:
            result = [a for a in result if a.category == category]
        return result

    async def decommission_asset(self, asset_id: str, reason: str = "") -> Asset:
        """Decommission an asset, changing its status to DECOMMISSIONED."""
        asset = self._assets.get(asset_id)
        if asset is None:
            raise AssetNotFoundError(f"Asset not found: {asset_id}")
        previous_status = asset.status
        updated = asset.model_copy(
            update={"status": AssetStatus.DECOMMISSIONED, "updated_at": utc_now()}
        )
        self._assets[asset_id] = updated
        AssetDecommissioned(
            asset_id=asset_id,
            previous_status=previous_status,
            reason=reason,
        )
        self._log.info("assetinv.asset.decommissioned", asset_id=asset_id, reason=reason)
        return updated

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics about the inventory."""
        total = len(self._assets)
        by_status: dict[str, int] = {}
        total_value = 0.0
        for asset in self._assets.values():
            by_status[asset.status.value] = by_status.get(asset.status.value, 0) + 1
            total_value += asset.current_value
        return {
            "total_assets": total,
            "by_status": by_status,
            "total_value": round(total_value, 2),
        }


__all__ = ["AssetInventory"]
