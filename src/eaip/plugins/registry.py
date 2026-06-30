"""Registry of installed plugins (independent of activation state)."""

from __future__ import annotations

from eaip.plugins.plugin import Plugin
from eaip.registry.registry import Registry


class PluginRegistry:
    """Tracks installed plugins; activation/deactivation is handled by the loader."""

    def __init__(self) -> None:
        self._inner: Registry[Plugin] = Registry(name="plugins", value_type=Plugin)  # type: ignore[type-abstract]

    def register(self, plugin: Plugin, *, replace: bool = False) -> None:
        self._inner.register(plugin.manifest.name, plugin, replace=replace)

    def unregister(self, name: str) -> bool:
        return self._inner.unregister(name)

    def get(self, name: str) -> Plugin:
        return self._inner.get(name)

    def has(self, name: str) -> bool:
        return self._inner.has(name)

    def all(self) -> list[Plugin]:
        return self._inner.values()

    def __len__(self) -> int:
        return len(self._inner)

    def __contains__(self, name: str) -> bool:
        return name in self._inner


__all__ = ["PluginRegistry"]
