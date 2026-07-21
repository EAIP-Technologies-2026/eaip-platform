"""ProviderRegistry — an observable registry of provider instances."""

from __future__ import annotations

from collections.abc import Callable

from eaip.providers.models import ProviderInstance
from eaip.registry.registry import Observer, Registry


class ProviderRegistry:
    """Wraps a generic Registry[ProviderInstance] with provider helpers."""

    def __init__(self) -> None:
        """Initialize the ProviderRegistry."""
        self._inner: Registry[ProviderInstance] = Registry(
            name="providers", value_type=ProviderInstance
        )

    def register(self, instance: ProviderInstance, *, replace: bool = False) -> None:
        """Register a provider instance.

        Args:
            instance: The provider instance to register.
            replace: If True, replace an existing provider with the same name.
        """
        self._inner.register(instance.name, instance, replace=replace)

    def unregister(self, provider_name: str) -> bool:
        """Remove a provider by name.

        Args:
            provider_name: The name of the provider to remove.

        Returns:
            True if the provider existed, False otherwise.
        """
        return self._inner.unregister(provider_name)

    def get(self, provider_name: str) -> ProviderInstance:
        """Get a provider by name.

        Args:
            provider_name: The name of the provider.

        Returns:
            The provider instance.

        Raises:
            NotFoundError: If the provider is not in the registry.
        """
        return self._inner.get(provider_name)

    def try_get(self, provider_name: str) -> ProviderInstance | None:
        """Get a provider by name, or None if not found.

        Args:
            provider_name: The name of the provider.

        Returns:
            The provider instance, or None.
        """
        return self._inner.try_get(provider_name)

    def all(self) -> list[ProviderInstance]:
        """Return all registered providers."""
        return self._inner.values()

    def available(self) -> list[ProviderInstance]:
        """Return only providers with AVAILABLE status."""
        return [p for p in self._inner.values() if p.status.name == "AVAILABLE"]

    def clear(self) -> None:
        """Remove all providers from the registry."""
        self._inner.clear()

    def observe(self, observer: Observer[ProviderInstance]) -> Callable[[], None]:
        """Register an observer for registry changes."""
        return self._inner.observe(observer)

    def __len__(self) -> int:
        """Return the number of registered providers."""
        return len(self._inner)

    def __contains__(self, provider_name: str) -> bool:
        """Check if a provider name is registered."""
        return provider_name in self._inner


__all__ = ["ProviderRegistry"]
