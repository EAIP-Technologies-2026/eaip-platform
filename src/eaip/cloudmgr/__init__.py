"""Multi-Cloud Resource Manager — register cloud providers, discover resources, compare costs."""

from __future__ import annotations

from eaip.cloudmgr.events import (
    CostCompared,
    ProviderRegistered,
    ResourceDiscovered,
)
from eaip.cloudmgr.exceptions import (
    CloudManagerError,
    ProviderNotFoundError,
)
from eaip.cloudmgr.health import CloudManagerHealthCheck
from eaip.cloudmgr.integration import CloudManagerRuntimeModule
from eaip.cloudmgr.manager import CloudResourceManager
from eaip.cloudmgr.models import (
    CloudConfig,
    CloudProvider,
    CloudResource,
    CostEstimate,
)

__all__ = [
    "CloudConfig",
    "CloudManagerError",
    "CloudManagerHealthCheck",
    "CloudManagerRuntimeModule",
    "CloudProvider",
    "CloudResource",
    "CloudResourceManager",
    "CostCompared",
    "CostEstimate",
    "ProviderNotFoundError",
    "ProviderRegistered",
    "ResourceDiscovered",
]
