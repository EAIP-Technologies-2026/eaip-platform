"""Dependency validation and topological ordering for plugins."""

from __future__ import annotations

from collections.abc import Iterable

from eaip.exceptions.domain import PluginError
from eaip.logging.context import get_logger
from eaip.plugins.plugin import Plugin, PluginManifest

_SEMVER_PARTS = 3


def _parse_semver(version: str) -> tuple[int, int, int]:
    """Parse a semver string into a (major, minor, patch) tuple."""
    parts = version.strip().split(".", 2)
    if len(parts) != _SEMVER_PARTS:
        raise ValueError(f"invalid semver {version!r}")
    return int(parts[0]), int(parts[1]), int(parts[2].split("+")[0].split("-")[0])


def _check_ge(version: tuple[int, int, int], spec: str) -> bool:
    return version >= _parse_semver(spec[2:])


def _check_gt(version: tuple[int, int, int], spec: str) -> bool:
    return version > _parse_semver(spec[1:])


def _check_le(version: tuple[int, int, int], spec: str) -> bool:
    return version <= _parse_semver(spec[2:])


def _check_lt(version: tuple[int, int, int], spec: str) -> bool:
    return version < _parse_semver(spec[1:])


def _check_pessimistic(version: tuple[int, int, int], spec: str) -> bool:
    comp = _parse_semver(spec[1:])
    if version < comp:
        return False
    return version < (comp[0], comp[1] + 1, 0)


def _check_compatible(version: tuple[int, int, int], spec: str) -> bool:
    comp = _parse_semver(spec[1:])
    if version < comp:
        return False
    return version < (comp[0] + 1, 0, 0)


def _check_range(version: str, spec: str) -> bool:
    parts = [s.strip() for s in spec.split(",", 1)]
    return all(_satisfies(version, p) for p in parts)


def _dispatch(version: tuple[int, int, int], spec: str) -> bool:
    """Dispatch to the appropriate checker based on spec prefix."""
    prefixes = {
        ">=": _check_ge,
        ">": _check_gt,
        "<=": _check_le,
        "<": _check_lt,
        "~": _check_pessimistic,
        "^": _check_compatible,
    }
    for prefix, checker in prefixes.items():
        if spec.startswith(prefix):
            return checker(version, spec)
    return _parse_semver(spec) == version


def _satisfies(version: str, spec: str) -> bool:
    """Check if *version* satisfies a semver range spec.

    Supported spec formats:
    - ``*`` or ``""`` — any version
    - ``>=1.0.0`` — greater than or equal
    - ``>=1.0.0,<2.0.0`` — range
    - ``~1.2.0`` — pessimistic (>=1.2.0, <1.3.0)
    - ``^1.2.3`` — compatible (>=1.2.3, <2.0.0)
    - ``1.2.3`` — exact match
    """
    if not spec or spec == "*":
        return True

    if "," in spec:
        return _check_range(version, spec)

    v = _parse_semver(version)
    return _dispatch(v, spec)


class PluginDependencyValidator:
    """Validates plugin inter-dependencies and produces activation order."""

    def __init__(self) -> None:
        """Initialize the validator."""
        self._log = get_logger("eaip.plugins.dependency")

    def validate(
        self,
        plugin: Plugin,
        available: dict[str, Plugin],
    ) -> list[str]:
        """Validate that all dependencies of *plugin* are satisfied.

        Args:
            plugin: The plugin whose dependencies to check.
            available: A dict of ``name -> Plugin`` for all installed plugins.

        Returns:
            A list of missing or unsatisfied dependency names (empty if valid).
        """
        errors: list[str] = []
        for dep in plugin.manifest.dependencies:
            if dep.name not in available:
                if not dep.optional:
                    errors.append(
                        f"missing required dependency {dep.name!r} "
                        f"(required by {plugin.manifest.name!r})",
                    )
                continue

            dep_plugin = available[dep.name]
            if not _satisfies(dep_plugin.manifest.version, dep.version_spec):
                msg = (
                    f"dependency {dep.name!r} version {dep_plugin.manifest.version} "
                    f"does not satisfy spec {dep.version_spec!r} "
                    f"(required by {plugin.manifest.name!r})"
                )
                if dep.optional:
                    self._log.warning(
                        "plugin.dependency.optional_mismatch",
                        plugin=plugin.manifest.name,
                        dependency=dep.name,
                        version=dep_plugin.manifest.version,
                        spec=dep.version_spec,
                    )
                else:
                    errors.append(msg)

        return errors

    def topological_sort(self, plugins: Iterable[Plugin]) -> list[Plugin]:
        """Return plugins in dependency order (dependencies before dependents).

        Uses Kahn's algorithm for topological sort. Raises
        ``PluginError`` on circular dependencies.

        Args:
            plugins: Iterable of Plugin instances.

        Returns:
            Plugins sorted so that every plugin appears after its dependencies.

        Raises:
            PluginError: If a circular dependency is detected.
        """
        plugin_list = list(plugins)
        manifest_map: dict[str, PluginManifest] = {p.manifest.name: p.manifest for p in plugin_list}
        plugin_map: dict[str, Plugin] = {p.manifest.name: p for p in plugin_list}

        in_degree: dict[str, int] = {p.manifest.name: 0 for p in plugin_list}
        dependents: dict[str, list[str]] = {p.manifest.name: [] for p in plugin_list}

        for plugin in plugin_list:
            for dep in plugin.manifest.dependencies:
                if dep.name in manifest_map and not dep.optional:
                    in_degree[plugin.manifest.name] = in_degree.get(plugin.manifest.name, 0) + 1
                    dependents.setdefault(dep.name, []).append(plugin.manifest.name)

        queue = [name for name, degree in in_degree.items() if degree == 0]
        sorted_names: list[str] = []

        while queue:
            name = queue.pop(0)
            sorted_names.append(name)
            for dependent in dependents.get(name, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(sorted_names) != len(plugin_list):
            circular = [n for n, d in in_degree.items() if d > 0]
            raise PluginError(
                f"circular dependency detected among plugins: {circular}",
                context={"plugins": circular},
            )

        return [plugin_map[name] for name in sorted_names]


__all__ = ["PluginDependencyValidator", "_satisfies"]
