"""CloudResourceManager — registers cloud providers, discovers resources, and compares costs."""

from __future__ import annotations

from eaip.cloudmgr.events import CostCompared, ProviderRegistered, ResourceDiscovered
from eaip.cloudmgr.exceptions import ProviderNotFoundError
from eaip.cloudmgr.models import (
    CloudConfig,
    CloudProvider,
    CloudResource,
    CostEstimate,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class CloudResourceManager:
    """Central service for managing multi-cloud resources."""

    def __init__(self, config: CloudConfig | None = None) -> None:
        self._config = config or CloudConfig()
        self._providers: dict[str, CloudProvider] = {}
        self._resources: dict[str, CloudResource] = {}
        self._log = get_logger("eaip.cloudmgr.manager")

    @property
    def config(self) -> CloudConfig:
        return self._config

    async def register_provider(self, provider: CloudProvider) -> CloudProvider:
        """Register a new cloud provider."""
        self._providers[provider.id] = provider
        event = ProviderRegistered(
            provider_id=provider.id,
            name=provider.name,
            provider_type=provider.provider_type.value,
        )
        self._log.info("cloudmgr.provider.registered", provider_id=provider.id)
        return provider

    async def discover_resources(self, provider_id: str) -> list[CloudResource]:
        """Discover resources for a given provider."""
        provider = self._providers.get(provider_id)
        if provider is None:
            raise ProviderNotFoundError(f"Provider '{provider_id}' not found")

        discovered: list[CloudResource] = []
        for rid, resource in self._resources.items():
            if resource.provider_id == provider_id:
                discovered.append(resource)

        for res in discovered:
            event = ResourceDiscovered(
                resource_id=res.id,
                provider_id=provider_id,
                resource_type=res.resource_type,
                name=res.name,
            )

        self._log.info(
            "cloudmgr.resources.discovered", provider_id=provider_id, count=len(discovered)
        )
        return discovered

    async def add_resource(self, resource: CloudResource) -> CloudResource:
        """Add a discovered cloud resource."""
        if resource.provider_id not in self._providers:
            raise ProviderNotFoundError(f"Provider '{resource.provider_id}' not found")
        self._resources[resource.id] = resource
        event = ResourceDiscovered(
            resource_id=resource.id,
            provider_id=resource.provider_id,
            resource_type=resource.resource_type,
            name=resource.name,
        )
        self._log.info("cloudmgr.resource.added", resource_id=resource.id)
        return resource

    async def compare_costs(self, resource_type: str) -> CostEstimate:
        """Compare costs for a given resource type across providers."""
        matching = [r for r in self._resources.values() if r.resource_type == resource_type]

        estimates: dict[str, float] = {}
        for res in matching:
            current = estimates.get(res.provider_id, 0.0)
            estimates[res.provider_id] = current + res.cost_per_hour

        estimate = CostEstimate(
            id=f"ce_{utc_now().timestamp():.0f}",
            resource_type=resource_type,
            estimates=estimates,
        )
        event = CostCompared(
            estimate_id=estimate.id,
            resource_type=resource_type,
            estimates=estimates,
        )
        self._log.info("cloudmgr.cost.compared", resource_type=resource_type)
        return estimate

    async def get_provider(self, provider_id: str) -> CloudProvider:
        """Retrieve a cloud provider by ID."""
        provider = self._providers.get(provider_id)
        if provider is None:
            raise ProviderNotFoundError(f"Provider '{provider_id}' not found")
        return provider

    async def list_providers(self) -> list[CloudProvider]:
        """List all registered cloud providers."""
        return list(self._providers.values())

    async def list_resources(self, provider_id: str | None = None) -> list[CloudResource]:
        """List all resources, optionally filtered by provider."""
        if provider_id is None:
            return list(self._resources.values())
        return [r for r in self._resources.values() if r.provider_id == provider_id]

    async def get_resource(self, resource_id: str) -> CloudResource:
        """Retrieve a cloud resource by ID."""
        resource = self._resources.get(resource_id)
        if resource is None:
            raise ProviderNotFoundError(f"Resource '{resource_id}' not found")
        return resource


__all__ = ["CloudResourceManager"]
