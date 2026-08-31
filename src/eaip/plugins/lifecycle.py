"""Plugin lifecycle manager — orchestrates discovery, validation, and activation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.exceptions.domain import PluginError
from eaip.logging.context import get_logger
from eaip.plugins.dependency import PluginDependencyValidator
from eaip.plugins.discovery import PluginDiscovery
from eaip.plugins.loader import PluginLoader
from eaip.plugins.plugin import Plugin

if TYPE_CHECKING:
    from eaip.platform.platform import Platform


class PluginLifecycleManager:
    """Orchestrates the full plugin lifecycle.

    Flow:
        1. ``discover_and_install()`` — find plugins via entry points / packages.
        2. ``validate_dependencies()`` — check all inter-plugin version constraints.
        3. ``resolve_activation_order()`` — topological sort by dependencies.
        4. ``activate_all(platform)`` — activate in dependency order.
        5. ``deactivate_all()`` — deactivate in reverse order.
    """

    def __init__(
        self,
        loader: PluginLoader,
        discovery: PluginDiscovery | None = None,
        validator: PluginDependencyValidator | None = None,
    ) -> None:
        """Initialize the lifecycle manager.

        Args:
            loader: The plugin loader instance.
            discovery: Optional discovery service (default: PluginDiscovery).
            validator: Optional dependency validator (default: PluginDependencyValidator).
        """
        self._loader = loader
        self._discovery = discovery or PluginDiscovery()
        self._validator = validator or PluginDependencyValidator()
        self._log = get_logger("eaip.plugins.lifecycle")

    async def discover_and_install(
        self,
        *,
        entry_point_group: str = "eaip.plugins",
        scan_packages: list[str] | None = None,
    ) -> list[Plugin]:
        """Discover plugins and install them into the registry.

        Args:
            entry_point_group: Entry point group to scan.
            scan_packages: Optional list of package names to scan recursively.

        Returns:
            List of newly installed plugins.
        """
        discovered: list[Plugin] = []
        discovered.extend(self._discovery.discover_entry_points(entry_point_group))
        if scan_packages:
            for pkg in scan_packages:
                discovered.extend(self._discovery.discover_package(pkg))

        installed: list[Plugin] = []
        for plugin in discovered:
            try:
                self._loader.install(plugin)
                installed.append(plugin)
            except BaseException as exc:
                self._log.error(
                    "plugin.install_failed",
                    plugin=plugin.manifest.name,
                    error=repr(exc),
                )
        return installed

    def validate_dependencies(self) -> list[str]:
        """Validate all installed plugin dependencies.

        Returns:
            A list of dependency error messages (empty if all valid).
        """
        available = {p.manifest.name: p for p in self._loader.all()}
        errors: list[str] = []
        for plugin in available.values():
            errors.extend(self._validator.validate(plugin, available))
        return errors

    def resolve_activation_order(self) -> list[Plugin]:
        """Return installed plugins in activation order (dependencies first).

        Returns:
            Plugins in topological order.

        Raises:
            PluginError: On circular dependency.
        """
        return self._validator.topological_sort(self._loader.all())

    async def activate_all(self, platform: Platform) -> None:
        """Activate all installed plugins in dependency order.

        Args:
            platform: The platform instance.

        Raises:
            PluginError: If any plugin fails to activate.
        """
        ordered = self.resolve_activation_order()
        self._log.info(
            "plugin.activate_all.start",
            count=len(ordered),
            order=[p.manifest.name for p in ordered],
        )
        failures: dict[str, BaseException] = {}
        for plugin in ordered:
            try:
                await self._loader.activate(plugin.manifest.name, platform)
            except BaseException as exc:
                failures[plugin.manifest.name] = exc
                self._log.error(
                    "plugin.activate_failed",
                    plugin=plugin.manifest.name,
                    error=repr(exc),
                )
        if failures:
            raise PluginError(
                f"{len(failures)} plugin(s) failed to activate",
                context={"failures": {n: str(e) for n, e in failures.items()}},
            )

    async def deactivate_all(self, platform: Platform) -> None:
        """Deactivate all active plugins in reverse order.

        Args:
            platform: The platform instance.
        """
        await self._loader.deactivate_all(platform)

    @property
    def loader(self) -> PluginLoader:
        """Return the underlying plugin loader."""
        return self._loader

    @property
    def discovery(self) -> PluginDiscovery:
        """Return the discovery service."""
        return self._discovery

    @property
    def validator(self) -> PluginDependencyValidator:
        """Return the dependency validator."""
        return self._validator


__all__ = ["PluginLifecycleManager"]
