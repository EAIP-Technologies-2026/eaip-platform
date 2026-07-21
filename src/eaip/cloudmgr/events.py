"""Domain events for multi-cloud resource management."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ProviderRegistered(DomainEvent):
    """Emitted when a cloud provider is registered."""

    event_type: ClassVar[str] = "eaip.cloudmgr.provider.registered"

    provider_id: str
    name: str
    provider_type: str


class ResourceDiscovered(DomainEvent):
    """Emitted when a new cloud resource is discovered."""

    event_type: ClassVar[str] = "eaip.cloudmgr.resource.discovered"

    resource_id: str
    provider_id: str
    resource_type: str
    name: str


class CostCompared(DomainEvent):
    """Emitted when a cost comparison is performed."""

    event_type: ClassVar[str] = "eaip.cloudmgr.cost.compared"

    estimate_id: str
    resource_type: str
    estimates: dict[str, float]


__all__ = [
    "CostCompared",
    "ProviderRegistered",
    "ResourceDiscovered",
]
