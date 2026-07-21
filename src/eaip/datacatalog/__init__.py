"""Enterprise Data Catalog — register data assets, discover by type/source, search, and track lineage."""

from __future__ import annotations

from eaip.datacatalog.catalog import DataCatalog
from eaip.datacatalog.events import (
    AssetRegistered,
    AssetRemoved,
    AssetUpdated,
)
from eaip.datacatalog.exceptions import (
    AssetNotFoundError,
    CatalogError,
)
from eaip.datacatalog.health import DataCatalogHealthCheck
from eaip.datacatalog.integration import DataCatalogRuntimeModule
from eaip.datacatalog.models import (
    AssetType,
    CatalogConfig,
    DataAsset,
    DataSource,
)

__all__ = [
    "AssetNotFoundError",
    "AssetRegistered",
    "AssetRemoved",
    "AssetType",
    "AssetUpdated",
    "CatalogConfig",
    "CatalogError",
    "DataAsset",
    "DataCatalog",
    "DataCatalogHealthCheck",
    "DataCatalogRuntimeModule",
    "DataSource",
]
