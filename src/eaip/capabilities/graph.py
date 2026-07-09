"""Capability dependency graph — DAG construction, cycle detection, topological order."""

from __future__ import annotations

from collections.abc import Iterable

from eaip.capabilities.capability import Capability
from eaip.exceptions.domain import DependencyCycleError, PluginError


class CapabilityGraph:
    """A directed acyclic graph (DAG) of capability dependencies.

    Builds an adjacency model from each capability's ``depends_on`` field
    and provides query methods for dependency traversal and ordering.
    """

    def __init__(self, capabilities: Iterable[Capability]) -> None:
        """Build the graph from an iterable of capabilities.

        Args:
            capabilities: Capabilities whose ``depends_on`` edges are
                used to construct the DAG.

        Raises:
            DependencyCycleError: If a cycle is detected during construction.
        """
        self._cap_map: dict[str, Capability] = {}
        self._deps: dict[str, list[str]] = {}  # node -> list of dependency names
        self._dependents: dict[str, list[str]] = {}  # node -> list of dependent names

        for cap in capabilities:
            self._cap_map[cap.name] = cap
            self._deps.setdefault(cap.name, [])
            self._dependents.setdefault(cap.name, [])
            for dep in cap.depends_on:
                if not dep.optional:
                    self._deps[cap.name].append(dep.name)
                    self._dependents.setdefault(dep.name, []).append(cap.name)

        cycle = self._detect_cycle()
        if cycle:
            raise DependencyCycleError(
                f"capability cycle detected: {' -> '.join(cycle)}",
                context={"cycle": cycle},
            )

    # ------------------------------------------------------------------
    # Public queries
    # ------------------------------------------------------------------

    def has(self, name: str) -> bool:
        """Check if a capability is in the graph."""
        return name in self._cap_map

    def get(self, name: str) -> Capability:
        """Get a capability by name.

        Raises:
            PluginError: If the capability is not in the graph.
        """
        if name not in self._cap_map:
            raise PluginError(f"capability {name!r} not in graph")
        return self._cap_map[name]

    def dependencies(self, name: str) -> list[str]:
        """Return the direct (non-optional) dependency names of *name*."""
        return list(self._deps.get(name, []))

    def dependents(self, name: str) -> list[str]:
        """Return names of capabilities that directly depend on *name*."""
        return list(self._dependents.get(name, []))

    def transitive_dependencies(self, name: str) -> list[str]:
        """Return all recursive dependency names (breadth-first).

        Args:
            name: The capability name.

        Returns:
            A list of dependency names in BFS order (excluding *name*).
        """
        visited: set[str] = set()
        queue: list[str] = list(self._deps.get(name, []))
        result: list[str] = []
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            result.append(current)
            queue.extend(d for d in self._deps.get(current, []) if d not in visited)
        return result

    def transitive_dependents(self, name: str) -> list[str]:
        """Return all capabilities that transitively depend on *name*.

        Args:
            name: The capability name.

        Returns:
            A list of dependent names in BFS order (excluding *name*).
        """
        visited: set[str] = set()
        queue: list[str] = list(self._dependents.get(name, []))
        result: list[str] = []
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            result.append(current)
            queue.extend(d for d in self._dependents.get(current, []) if d not in visited)
        return result

    def topological_sort(self) -> list[Capability]:
        """Return capabilities in dependency order (Kahn's algorithm).

        Returns:
            Capabilities sorted so dependencies precede their dependents.

        Raises:
            DependencyCycleError: If a cycle is detected.
        """
        in_degree: dict[str, int] = {n: len(self._deps[n]) for n in self._cap_map}
        queue = [n for n, d in in_degree.items() if d == 0]
        sorted_names: list[str] = []

        while queue:
            name = queue.pop(0)
            sorted_names.append(name)
            for dep_name in self._dependents.get(name, []):
                in_degree[dep_name] -= 1
                if in_degree[dep_name] == 0:
                    queue.append(dep_name)

        if len(sorted_names) != len(self._cap_map):
            remaining = [n for n, d in in_degree.items() if d > 0]
            raise DependencyCycleError(
                f"capability cycle detected among: {remaining}",
                context={"cycle": remaining},
            )

        return [self._cap_map[name] for name in sorted_names]

    @property
    def count(self) -> int:
        """Return the number of capabilities in the graph."""
        return len(self._cap_map)

    def __contains__(self, name: str) -> bool:
        """Check if a capability is in the graph."""
        return name in self._cap_map

    def __len__(self) -> int:
        """Return the number of capabilities in the graph."""
        return len(self._cap_map)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _detect_cycle(self) -> list[str] | None:
        """Detect a cycle using DFS.

        Returns:
            A list of node names forming a cycle, or None if acyclic.
        """
        _white, _gray, _black = 0, 1, 2
        colour: dict[str, int] = dict.fromkeys(self._cap_map, _white)

        def dfs(node: str, path: list[str]) -> list[str] | None:
            colour[node] = _gray
            path.append(node)
            for neighbour in self._deps.get(node, []):
                if neighbour not in colour:
                    continue
                if colour[neighbour] is _gray:
                    cycle_start = path.index(neighbour)
                    return [*path[cycle_start:], neighbour]
                if colour[neighbour] is _white:
                    result = dfs(neighbour, path)
                    if result:
                        return result
            path.pop()
            colour[node] = _black
            return None

        for node in list(self._cap_map):
            if colour[node] is _white:
                result = dfs(node, [])
                if result:
                    return result
        return None


__all__ = ["CapabilityGraph"]
