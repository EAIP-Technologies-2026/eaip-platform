"""Capability resolution — semver-based matching and best-version selection."""

from __future__ import annotations

from eaip.capabilities.capability import Capability
from eaip.capabilities.graph import CapabilityGraph
from eaip.plugins.dependency import _satisfies


class CapabilityResolver:
    """Resolves capability references to concrete capability instances."""

    def resolve(
        self,
        graph: CapabilityGraph,
        name: str,
        version_spec: str = "*",
    ) -> Capability | None:
        """Find the best matching capability in a graph.

        If *version_spec* is ``*`` or empty, returns the capability as-is.
        Otherwise checks that the capability's version satisfies *version_spec*.

        Args:
            graph: The capability dependency graph.
            name: The capability name.
            version_spec: Semver range spec.

        Returns:
            The matching capability, or None if not found or version mismatch.
        """
        if not graph.has(name):
            return None
        cap = graph.get(name)
        if version_spec and version_spec != "*" and not _satisfies(cap.version, version_spec):
            return None
        return cap

    def resolve_all(
        self,
        graph: CapabilityGraph,
        requirements: dict[str, str],
    ) -> dict[str, Capability]:
        """Resolve multiple capability requirements at once.

        Args:
            graph: The capability dependency graph.
            requirements: A dict of ``name -> version_spec``.

        Returns:
            A dict of ``name -> Capability`` for successfully resolved
            capabilities. Failed resolutions are omitted.

        Raises:
            ValueError: If any required capability is missing from the graph.
        """
        result: dict[str, Capability] = {}
        missing: list[str] = []
        for name, spec in requirements.items():
            cap = self.resolve(graph, name, spec)
            if cap is None:
                missing.append(f"{name} (spec={spec!r})")
            else:
                result[name] = cap
        if missing:
            raise ValueError(
                f"unresolved capabilities: {', '.join(missing)}",
            )
        return result


__all__ = ["CapabilityResolver"]
