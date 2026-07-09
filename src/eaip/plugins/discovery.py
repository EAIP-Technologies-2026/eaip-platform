"""Plugin discovery — entry-point and filesystem scanning for EAIP plugins."""

from __future__ import annotations

import importlib
import importlib.metadata
import pkgutil
from typing import Any

from eaip.logging.context import get_logger
from eaip.plugins.plugin import Plugin


class PluginDiscovery:
    """Discovers plugin classes from entry points and Python packages."""

    def __init__(self) -> None:
        """Initialize the discovery service."""
        self._log = get_logger("eaip.plugins.discovery")

    def discover_entry_points(self, group: str = "eaip.plugins") -> list[Plugin]:
        """Discover plugins registered via the given entry point group.

        Uses ``importlib.metadata.entry_points()`` to find installed
        packages that advertise an ``eaip.plugins`` entry point.
        Each entry point must resolve to a :class:`Plugin` instance.

        Args:
            group: The entry point group to scan (default ``eaip.plugins``).

        Returns:
            A list of discovered :class:`Plugin` instances.
        """
        plugins: list[Plugin] = []
        eps = importlib.metadata.entry_points(group=group)
        for ep in eps:
            try:
                obj = ep.load()
                if isinstance(obj, Plugin):
                    plugins.append(obj)
                    self._log.info(
                        "plugin.discovered.entry_point",
                        plugin=ep.name,
                        module=ep.value,
                    )
                else:
                    self._log.warning(
                        "plugin.skipped.not_a_plugin",
                        name=ep.name,
                        module=ep.value,
                        type=type(obj).__name__,
                    )
            except BaseException as exc:
                self._log.error(
                    "plugin.discovery.entry_point_failed",
                    name=ep.name,
                    module=ep.value,
                    error=repr(exc),
                )
        return plugins

    def discover_module(self, module_name: str) -> list[Plugin]:
        """Import a module and extract all :class:`Plugin` instances.

        Scans the module's public members for objects that satisfy the
        :class:`Plugin` protocol.

        Args:
            module_name: Fully-qualified module name (e.g. ``eaip_foo.plugin``).

        Returns:
            A list of :class:`Plugin` instances found in the module.
        """
        plugins: list[Plugin] = []
        try:
            mod = importlib.import_module(module_name)
        except BaseException as exc:
            self._log.error(
                "plugin.discovery.module_import_failed",
                module=module_name,
                error=repr(exc),
            )
            return plugins

        for name in dir(mod):
            if name.startswith("_"):
                continue
            obj = getattr(mod, name)
            if isinstance(obj, Plugin):
                plugins.append(obj)
                self._log.info(
                    "plugin.discovered.module",
                    plugin=name,
                    module=module_name,
                )
        return plugins

    def discover_package(self, package_name: str) -> list[Plugin]:
        """Recursively scan a package for :class:`Plugin` instances.

        Walks all submodules of *package_name* and collects any Plugin
        instances found.

        Args:
            package_name: Fully-qualified package name.

        Returns:
            A list of :class:`Plugin` instances.
        """
        plugins: list[Plugin] = []
        try:
            pkg = importlib.import_module(package_name)
        except BaseException as exc:
            self._log.error(
                "plugin.discovery.package_import_failed",
                package=package_name,
                error=repr(exc),
            )
            return plugins

        seen_modules: set[str] = set()

        def _walk(module: Any, prefix: str) -> None:
            for _importer, modname, _ispkg in pkgutil.walk_packages(
                module.__path__,
                prefix=f"{prefix}.",
            ):
                full_name = f"{prefix}.{modname}" if prefix else modname
                if full_name in seen_modules:
                    continue
                seen_modules.add(full_name)
                try:
                    sub_mod = importlib.import_module(full_name)
                except BaseException:
                    self._log.debug(
                        "plugin.discovery.skip_submodule",
                        module=full_name,
                    )
                    continue
                for name in dir(sub_mod):
                    if name.startswith("_"):
                        continue
                    obj = getattr(sub_mod, name)
                    if isinstance(obj, Plugin):
                        plugins.append(obj)
                        self._log.info(
                            "plugin.discovered.package_submodule",
                            plugin=name,
                            module=full_name,
                        )

        _walk(pkg, package_name)
        if not plugins:
            for name in dir(pkg):
                if name.startswith("_"):
                    continue
                obj = getattr(pkg, name)
                if isinstance(obj, Plugin):
                    plugins.append(obj)
                    self._log.info(
                        "plugin.discovered.package",
                        plugin=name,
                        package=package_name,
                    )

        return plugins


__all__ = ["PluginDiscovery"]
