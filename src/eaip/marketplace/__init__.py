"""Agent & Plugin Marketplace — discover, publish, and manage packages."""

from __future__ import annotations

from eaip.marketplace.discovery import DiscoveryService
from eaip.marketplace.events import (
    PackageDeprecated,
    PackageDownloaded,
    PackageInstalled,
    PackagePublished,
    PackageUninstalled,
    PackageUpdated,
)
from eaip.marketplace.exceptions import (
    DependencyNotSatisfiedError,
    MarketplaceError,
    PackageAlreadyInstalledError,
    PackageNotCompatibleError,
    PackageNotFoundError,
)
from eaip.marketplace.health import MarketplaceHealthCheck
from eaip.marketplace.integration import MarketplaceRuntimeModule
from eaip.marketplace.manager import PackageManager
from eaip.marketplace.models import (
    MarketplacePackage,
    PackageInstallation,
    PackageStatus,
    PackageType,
    PackageVersion,
)
from eaip.marketplace.publisher import Publisher
from eaip.marketplace.registry import MarketplaceRegistry

__all__ = [
    "DependencyNotSatisfiedError",
    "DiscoveryService",
    "MarketplaceError",
    "MarketplaceHealthCheck",
    "MarketplacePackage",
    "MarketplaceRegistry",
    "MarketplaceRuntimeModule",
    "PackageAlreadyInstalledError",
    "PackageDeprecated",
    "PackageDownloaded",
    "PackageInstallation",
    "PackageInstalled",
    "PackageManager",
    "PackageNotCompatibleError",
    "PackageNotFoundError",
    "PackagePublished",
    "PackageStatus",
    "PackageType",
    "PackageUninstalled",
    "PackageUpdated",
    "PackageVersion",
    "Publisher",
]
