"""Dependency graph — impact analysis, critical paths, and adjacency."""

from __future__ import annotations

from collections import deque
from typing import Any

from eaip.healthagg.exceptions import DependencyNotFoundError
from eaip.healthagg.models import HealthDependency


class DependencyGraph:
    def __init__(self) -> None:
        self._dependencies: dict[str, HealthDependency] = {}

    def register_dependency(
        self,
        source: str,
        target: str,
        dependency_type: str = "hard",
        optional: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> HealthDependency:
        dep_id = f"{source}->{target}"
        dep = HealthDependency(
            id=dep_id,
            source_component=source,
            target_component=target,
            dependency_type=dependency_type,
            optional=optional,
            metadata=metadata or {},
        )
        self._dependencies[dep_id] = dep
        return dep

    def _get_dependency(self, dep_id: str) -> HealthDependency:
        dep = self._dependencies.get(dep_id)
        if dep is None:
            raise DependencyNotFoundError(
                f"dependency {dep_id!r} not found",
                context={"dependency_id": dep_id},
            )
        return dep

    async def build_graph(self) -> dict[str, set[str]]:
        """Return adjacency dict: component -> set of target components it depends on."""
        graph: dict[str, set[str]] = {}
        for dep in self._dependencies.values():
            graph.setdefault(dep.source_component, set()).add(dep.target_component)
            graph.setdefault(dep.target_component, set())
        return graph

    async def evaluate_impact(self, component_name: str) -> list[str]:
        """Return all components downstream of *component_name* affected by a failure."""
        graph = await self.build_graph()
        reverse: dict[str, set[str]] = {}
        for src, targets in graph.items():
            for tgt in targets:
                reverse.setdefault(tgt, set()).add(src)

        affected: list[str] = []
        queue: deque[str] = deque([component_name])
        visited: set[str] = set()

        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            if node != component_name:
                affected.append(node)
            for upstream in reverse.get(node, set()):
                dep_id = f"{upstream}->{node}"
                dep = self._dependencies.get(dep_id)
                if dep is None or dep.optional:
                    continue
                queue.append(upstream)

        return affected

    async def get_upstream_dependencies(self, component: str) -> list[HealthDependency]:
        """Return all dependencies where *component* depends on something else."""
        result: list[HealthDependency] = []
        for dep in self._dependencies.values():
            if dep.source_component == component:
                result.append(dep)
        return result

    async def get_downstream_dependents(self, component: str) -> list[HealthDependency]:
        """Return all dependencies where something else depends on *component*."""
        result: list[HealthDependency] = []
        for dep in self._dependencies.values():
            if dep.target_component == component:
                result.append(dep)
        return result

    async def get_critical_path(self, component: str) -> list[str]:
        """Return the chain of hard dependencies leading from *component* upstream."""
        path: list[str] = [component]
        visited: set[str] = {component}
        current = component
        while True:
            upstream = await self.get_upstream_dependencies(current)
            hard = [d for d in upstream if d.dependency_type == "hard" and not d.optional]
            if not hard:
                break
            next_comp = hard[0].target_component
            if next_comp in visited:
                break
            visited.add(next_comp)
            path.append(next_comp)
            current = next_comp
        return path


__all__ = ["DependencyGraph"]
