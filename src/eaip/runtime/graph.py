"""DependencyGraph — topological ordering for runtime module startup.

The :class:`DependencyGraph` accepts a collection of
:class:`~eaip.runtime.module.RuntimeModule` instances and returns them in an
order that respects their declared :attr:`~eaip.runtime.module.RuntimeModule.dependencies`.

Algorithm
---------
Kahn's algorithm (BFS-based) — O(V + E), deterministic, detects cycles.

Invariants
----------
- Every dependency name must resolve to a registered module; unknown names
  raise :class:`~eaip.runtime.exceptions.DependencyResolutionError`.
- Cyclic graphs raise :class:`~eaip.runtime.exceptions.DependencyResolutionError`
  with a description of the cycle.
- Modules with equal depth are sorted alphabetically for reproducibility.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import TYPE_CHECKING

from eaip.runtime.exceptions import DependencyResolutionError

if TYPE_CHECKING:  # pragma: no cover
    from eaip.runtime.module import RuntimeModule


class DependencyGraph:
    """Resolves module startup order via topological sort."""

    def __init__(self, modules: list[RuntimeModule]) -> None:
        self._modules: dict[str, RuntimeModule] = {}
        for mod in modules:
            if mod.name in self._modules:
                raise DependencyResolutionError(
                    f"duplicate module name {mod.name!r}",
                    context={"name": mod.name},
                )
            self._modules[mod.name] = mod

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ordered(self) -> list[RuntimeModule]:
        """Return modules in valid startup order (dependencies before dependants).

        Raises :class:`~eaip.runtime.exceptions.DependencyResolutionError` if
        the graph contains unknown references or a cycle.
        """
        self._validate_references()
        return self._kahn_sort()

    def names(self) -> list[str]:
        """Sorted list of all registered module names."""
        return sorted(self._modules)

    def __len__(self) -> int:
        return len(self._modules)

    def __contains__(self, name: str) -> bool:
        return name in self._modules

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _validate_references(self) -> None:
        """Ensure every declared dependency resolves to a known module."""
        for name, mod in self._modules.items():
            for dep in mod.dependencies:
                if dep not in self._modules:
                    raise DependencyResolutionError(
                        f"module {name!r} declares unknown dependency {dep!r}",
                        context={"module": name, "missing_dependency": dep},
                    )

    def _kahn_sort(self) -> list[RuntimeModule]:
        """Kahn's topological sort; raises on cycles."""
        # Build adjacency list and in-degree map.
        # dep → list of modules that depend on dep
        dependants: dict[str, list[str]] = defaultdict(list)
        in_degree: dict[str, int] = dict.fromkeys(self._modules, 0)

        for name, mod in self._modules.items():
            for dep in mod.dependencies:
                dependants[dep].append(name)
                in_degree[name] += 1

        # Initialise queue with all zero-in-degree nodes, sorted for determinism.
        queue: deque[str] = deque(
            sorted(name for name, deg in in_degree.items() if deg == 0)
        )
        result: list[RuntimeModule] = []

        while queue:
            name = queue.popleft()
            result.append(self._modules[name])
            # For each module that depends on *name*, reduce its in-degree.
            for dependant in sorted(dependants.get(name, [])):
                in_degree[dependant] -= 1
                if in_degree[dependant] == 0:
                    queue.append(dependant)

        if len(result) != len(self._modules):
            # Cycle: find the unprocessed nodes for the error message.
            unprocessed = sorted(
                name for name, deg in in_degree.items() if deg > 0
            )
            raise DependencyResolutionError(
                "circular dependency detected among modules",
                context={"cycle_candidates": unprocessed},
            )

        return result


__all__ = ["DependencyGraph"]
