"""ProviderDiscovery — discovers and registers providers from configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.providers.models import ProviderInstance, ProviderStatus

if TYPE_CHECKING:
    from eaip.providers.registry import ProviderRegistry


class ProviderDiscovery:
    """Discovers AI provider instances and registers them.

    Supports registration of pre-configured providers and
    environment-based auto-discovery (future: DNS, container orchestration).
    """

    def __init__(self, registry: ProviderRegistry) -> None:
        """Initialize the ProviderDiscovery.

        Args:
            registry: The provider registry to register instances into.
        """
        self._registry = registry
        self._log = get_logger("eaip.providers.discovery")

    def register_instance(self, instance: ProviderInstance) -> None:
        """Register a single provider instance.

        Args:
            instance: The provider instance to register.
        """
        self._registry.register(instance)
        self._log.info(
            "provider.discovery.registered",
            provider=instance.name,
            type=instance.provider_type,
            endpoint=instance.endpoint,
            models=len(instance.models),
        )

    def discover_from_config(
        self,
        configs: list[dict[str, str]],
    ) -> list[ProviderInstance]:
        """Discover and register providers from a list of configuration dicts.

        Each config dict should contain:
        - name, provider_type, endpoint, api_key, default_model.

        Args:
            configs: A list of provider configuration dictionaries.

        Returns:
            The list of registered provider instances.
        """
        instances: list[ProviderInstance] = []
        for cfg in configs:
            instance = ProviderInstance(
                name=cfg.get("name", "unknown"),
                provider_type=cfg.get("provider_type", "openai_compat"),
                endpoint=cfg.get("endpoint", ""),
                api_key=cfg.get("api_key", ""),
                default_model=cfg.get("default_model", ""),
                status=ProviderStatus.UNAVAILABLE,
            )
            try:
                self.register_instance(instance)
                instances.append(instance)
            except Exception as exc:
                self._log.error(
                    "provider.discovery.failed",
                    provider=cfg.get("name"),
                    error=repr(exc),
                )
        return instances


__all__ = ["ProviderDiscovery"]
