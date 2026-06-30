"""Plugin loader — discovery, contract validation, activation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.exceptions.domain import (
    PluginContractViolationError,
    PluginError,
)
from eaip.logging.context import get_logger
from eaip.plugins.plugin import Plugin
from eaip.plugins.registry import PluginRegistry

if TYPE_CHECKING:  # pragma: no cover
    from eaip.platform.platform import Platform

#: The contract version this Foundation release implements. Plugins targeting
#: a different *major* contract version will be rejected.
CURRENT_CONTRACT_VERSION: str = "1.0.0"


class PluginLoader:
    """Validates plugin contracts, registers them, and orchestrates activation."""

    def __init__(self, registry: PluginRegistry) -> None:
        self._registry = registry
        self._activated: set[str] = set()
        self._log = get_logger("eaip.plugins.loader")

    @property
    def activated(self) -> list[str]:
        return sorted(self._activated)

    # ------------------------------------------------------------------
    # Installation & validation
    # ------------------------------------------------------------------
    def install(self, plugin: Plugin) -> None:
        """Register ``plugin`` after validating its contract."""
        self._validate_contract(plugin)
        self._registry.register(plugin)
        self._log.info(
            "plugin.installed",
            plugin=plugin.manifest.name,
            version=plugin.manifest.version,
        )

    def uninstall(self, name: str) -> bool:
        if name in self._activated:
            raise PluginError(
                f"cannot uninstall active plugin {name!r}; deactivate first",
                context={"plugin": name},
            )
        removed = self._registry.unregister(name)
        if removed:
            self._log.info("plugin.uninstalled", plugin=name)
        return removed

    @staticmethod
    def _validate_contract(plugin: Plugin) -> None:
        if not isinstance(plugin, Plugin):  # runtime_checkable Protocol
            raise PluginContractViolationError(
                "plugin does not satisfy the Plugin protocol",
                context={"plugin_type": type(plugin).__name__},
            )
        target_major = plugin.manifest.contract_version.split(".", 1)[0]
        current_major = CURRENT_CONTRACT_VERSION.split(".", 1)[0]
        if target_major != current_major:
            raise PluginContractViolationError(
                f"plugin targets contract major {target_major}; "
                f"platform implements {current_major}",
                context={
                    "plugin": plugin.manifest.name,
                    "plugin_contract": plugin.manifest.contract_version,
                    "platform_contract": CURRENT_CONTRACT_VERSION,
                },
            )

    # ------------------------------------------------------------------
    # Activation
    # ------------------------------------------------------------------
    async def activate(self, name: str, platform: "Platform") -> None:
        plugin = self._registry.get(name)
        if name in self._activated:
            return  # idempotent
        try:
            await plugin.activate(platform)
        except BaseException as exc:
            raise PluginError(
                f"plugin {name!r} failed to activate",
                context={"plugin": name},
                cause=exc,
            ) from exc
        self._activated.add(name)
        self._log.info("plugin.activated", plugin=name)

    async def deactivate(self, name: str, platform: "Platform") -> None:
        if name not in self._activated:
            return  # idempotent
        plugin = self._registry.get(name)
        try:
            await plugin.deactivate(platform)
        finally:
            self._activated.discard(name)
            self._log.info("plugin.deactivated", plugin=name)

    async def activate_all(self, platform: "Platform") -> None:
        for plugin in self._registry.all():
            await self.activate(plugin.manifest.name, platform)

    async def deactivate_all(self, platform: "Platform") -> None:
        # Reverse order of activation.
        for name in reversed(list(self._activated)):
            await self.deactivate(name, platform)


__all__ = ["CURRENT_CONTRACT_VERSION", "PluginLoader"]
