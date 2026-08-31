"""Capability discovery — scans plugins and packages for capability declarations."""

from __future__ import annotations

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.capabilities.registry import CapabilityRegistry
from eaip.logging.context import get_logger
from eaip.plugins.plugin import Plugin


class CapabilityDiscovery:
    """Discovers capabilities from plugins and registers them."""

    def __init__(self) -> None:
        """Initialize the discovery service."""
        self._log = get_logger("eaip.capabilities.discovery")

    def discover_from_plugin(
        self,
        plugin: Plugin,
        registry: CapabilityRegistry,
        *,
        replace: bool = False,
    ) -> list[Capability]:
        """Register capabilities declared in a plugin's manifest.

        Scans the plugin manifest's ``provides_capabilities`` (or ``tags``)
        and creates a ``Capability`` record for each entry.

        Args:
            plugin: The plugin whose capabilities to register.
            registry: The capability registry to register into.
            replace: Whether to replace existing capabilities.

        Returns:
            A list of capabilities registered.
        """
        manifest = plugin.manifest
        cap_names = manifest.provides_capabilities or manifest.tags
        registered: list[Capability] = []

        for cap_name in cap_names:
            capability = Capability(
                name=cap_name,
                title=f"{manifest.name}:{cap_name}",
                description=f"Provided by plugin {manifest.name}",
                version=manifest.version,
                status=CapabilityStatus.REGISTERED,
                tags=(manifest.name, *manifest.tags),
                metadata={"plugin": manifest.name},
            )
            try:
                registry.register(capability, replace=replace)
                registered.append(capability)
                self._log.info(
                    "capability.discovered.from_plugin",
                    capability=cap_name,
                    plugin=manifest.name,
                )
            except BaseException as exc:
                self._log.error(
                    "capability.discovery.failed",
                    capability=cap_name,
                    plugin=manifest.name,
                    error=repr(exc),
                )

        return registered

    def discover_from_plugins(
        self,
        plugins: list[Plugin],
        registry: CapabilityRegistry,
        *,
        replace: bool = False,
    ) -> list[Capability]:
        """Register capabilities from multiple plugins.

        Args:
            plugins: The plugins to scan.
            registry: The capability registry.
            replace: Whether to replace existing capabilities.

        Returns:
            All capabilities registered across all plugins.
        """
        all_caps: list[Capability] = []
        for plugin in plugins:
            all_caps.extend(self.discover_from_plugin(plugin, registry, replace=replace))
        return all_caps


__all__ = ["CapabilityDiscovery"]
