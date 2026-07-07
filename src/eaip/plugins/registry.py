"""Registry of installed plugins (independent of activation state)."""

from __future__ import annotations

from eaip.plugins.plugin import Plugin
from eaip.registry.registry import Registry


class PluginRegistry:
    """Tracks installed plugins; activation/deactivation is handled by the loader."""

    def __init__(self) -> None:
        """Initializes the plugin registry."""
        self._inner: Registry[Plugin] = Registry(name="plugins", value_type=Plugin)  # type: ignore[type-abstract]

    def register(self, plugin: Plugin, *, replace: bool = False) -> None:
        """Registers a plugin.

        Args:
            plugin: The plugin to register.
            replace: Whether to replace an existing plugin with the same name.
        """
        self._inner.register(plugin.manifest.name, plugin, replace=replace)

    def unregister(self, name: str) -> bool:
        """Unregisters a plugin by name.

        Args:
            name: The name of the plugin to unregister.

        Returns:
            True if the plugin was found and unregistered, False otherwise.
        """
        return self._inner.unregister(name)

    def get(self, name: str) -> Plugin:
        """Gets a plugin by name.

        Args:
            name: The name of the plugin.

        Returns:
            The plugin.
        """
        return self._inner.get(name)

    def has(self, name: str) -> bool:
        """Checks if a plugin exists.

        Args:
            name: The name of the plugin.

        Returns:
            True if the plugin exists, False otherwise.
        """
        return self._inner.has(name)

    def all(self) -> list[Plugin]:
        """Returns all registered plugins.

        Returns:
            A list of all registered plugins.
        """
        return self._inner.values()

    def __len__(self) -> int:
        """Returns the number of registered plugins."""
        return len(self._inner)

    def __contains__(self, name: str) -> bool:
        """Checks if a plugin exists in the registry.

        Args:
            name: The name of the plugin.

        Returns:
            True if the plugin exists, False otherwise.
        """
        return name in self._inner


__all__ = ["PluginRegistry"]
