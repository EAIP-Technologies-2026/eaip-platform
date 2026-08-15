"""Capability descriptors, registry, graph, discovery, resolution, health, and events."""

from __future__ import annotations

from eaip.capabilities.capability import (
    Capability,
    CapabilityCategory,
    CapabilityContract,
    CapabilityDependency,
    CapabilityStatus,
    OperationType,
)
from eaip.capabilities.discovery import CapabilityDiscovery
from eaip.capabilities.events import (
    CapabilityDeprecated,
    CapabilityDisabled,
    CapabilityEnabled,
    CapabilityHealthChanged,
    CapabilityRegistered,
    CapabilityUpgraded,
)
from eaip.capabilities.graph import CapabilityGraph
from eaip.capabilities.health import CapabilityHealthCheck
from eaip.capabilities.inventory import (
    CANONICAL_CAPABILITIES,
    load_canonical_inventory,
)
from eaip.capabilities.registry import CapabilityRegistry
from eaip.capabilities.resolution import CapabilityResolver

__all__ = [
    "CANONICAL_CAPABILITIES",
    "Capability",
    "CapabilityCategory",
    "CapabilityContract",
    "CapabilityDependency",
    "CapabilityDeprecated",
    "CapabilityDisabled",
    "CapabilityDiscovery",
    "CapabilityEnabled",
    "CapabilityGraph",
    "CapabilityHealthChanged",
    "CapabilityHealthCheck",
    "CapabilityRegistered",
    "CapabilityRegistry",
    "CapabilityResolver",
    "CapabilityStatus",
    "CapabilityUpgraded",
    "OperationType",
    "load_canonical_inventory",
]
